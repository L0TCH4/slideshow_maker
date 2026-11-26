"""写真とテロップを絵にする処理(画面にも動画にも使う)。GUI には依存しません。"""
import functools
import re
import sys
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .. import config


# ---------------------------------------------------------------- 1枚分の指定
@dataclass
class SlideSpec:
    """動画の1枚ぶんの材料。"""
    path: str
    caption: str = ""
    duration: float = 3.0       # この写真を出す秒数
    font_path: str = ""         # この写真のテロップのフォント
    text_color: str = ""        # この写真のテロップの色(#RRGGBB)


# ---------------------------------------------------------------- 色
_HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def is_hex_color(value):
    return bool(value) and bool(_HEX.match(value.strip()))


def parse_color(value, default=(255, 255, 255, 255)):
    """'#rrggbb' を (R, G, B, 255) にする。読めなければ default。"""
    if not is_hex_color(value or ""):
        return default
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), 255


def luminance(rgba):
    r, g, b = rgba[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


# ---------------------------------------------------------------- フォント・画像
def load_font(font_path, size):
    try:
        if font_path:
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    return ImageFont.load_default()


def _open_rgb(path):
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


@functools.lru_cache(maxsize=8)
def _open_rgb_small(path, max_side=2000):
    """プレビュー用: 大きな写真を縮めて覚えておく(何度も読み込まないため)。"""
    img = _open_rgb(path)
    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)
    return img


def fit_canvas(path, size, preview=False):
    """写真を、比率を保ったまま黒背景いっぱいに収めた画像を返す。"""
    W, H = size
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    try:
        img = _open_rgb_small(path) if preview else _open_rgb(path)
        img = ImageOps.contain(img, (W, H), Image.BILINEAR if preview else Image.LANCZOS)
        canvas.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
    except Exception as e:
        print(f"写真を読み込めませんでした: {path}: {e}", file=sys.stderr)
    return canvas


# ---------------------------------------------------------------- テロップ
def wrap_text(draw, text, font, max_width):
    """文字単位で折り返す(日本語対応)。入力された改行もそのまま反映する。"""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if cur and draw.textlength(cur + ch, font=font) > max_width:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


def make_overlay(caption, size, font_path, font_pct, pos_pct, text_color=None, style=None):
    """テロップ(帯 + 文字)だけを描いた透明な画像を返す。文字がなければ None。

    font_pct  : 文字の大きさ(画面の高さに対する%)
    pos_pct   : 高さの位置 0(いちばん上)〜100(いちばん下)
    text_color: 文字の色 '#rrggbb'(なければ config.DEFAULTS["text_color"])
    """
    st = style or config.TELOP_STYLE
    caption = (caption or "").strip("\n")
    if not caption.strip():
        return None
    W, H = size
    font = load_font(font_path, max(10, int(H * font_pct / 100)))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    tc = parse_color(text_color or config.DEFAULTS["text_color"])
    band = tuple(st["band_color"])
    stroke_color = tuple(st["stroke_color"])
    if st.get("auto_contrast", True) and luminance(tc) < 0.45:   # 暗い文字 → 明るい帯とフチ
        band = (255, 255, 255, band[3])
        stroke_color = (255, 255, 255, 255)

    lines = wrap_text(d, caption, font, W - int(W * st["side_margin"] * 2))
    fs = getattr(font, "size", 20)
    line_h = int(fs * st["line_spacing"])
    pad = int(fs * st["band_padding"])
    block_h = line_h * len(lines) + pad * 2

    margin = int(H * st["v_margin"])
    y0 = margin + int(max(0, H - block_h - margin * 2) * pos_pct / 100)

    d.rectangle([0, y0, W, y0 + block_h], fill=band)
    stroke = max(1, fs // 14)
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=font)
        d.text(((W - tw) / 2, y0 + pad + i * line_h), line, font=font,
               fill=tc, stroke_width=stroke, stroke_fill=stroke_color)
    return overlay


# ---------------------------------------------------------------- プレビュー
def render_photo_preview(path, avail):
    """写真だけを、表示エリア(avail=(幅, 高さ))に収めて返す。"""
    w, h = max(2, int(avail[0])), max(2, int(avail[1]))
    try:
        img = _open_rgb_small(path).copy()
    except Exception:
        return None
    img.thumbnail((w, h), Image.BILINEAR)
    return img


def render_preview(path, caption, shape_size, avail, font_path, font_pct, pos_pct,
                   text_color=None):
    """動画の形(shape_size)で、テロップ入りの仕上がりイメージを返す。"""
    W, H = shape_size
    scale = min(max(avail[0], 2) / W, max(avail[1], 2) / H)
    size = (max(2, int(W * scale)), max(2, int(H * scale)))
    img = fit_canvas(path, size, preview=True)
    ov = make_overlay(caption, size, font_path, font_pct, pos_pct, text_color=text_color)
    if ov is not None:
        img.paste(ov, (0, 0), ov)
    return img


# ---------------------------------------------------------------- 動画用スライド
class Slide:
    """動画に使う1枚分。frame(r) に 0〜1 を渡すと、その時点の1コマを返す。"""

    def __init__(self, spec: SlideSpec, index, size, kenburns, font_pct, pos_pct):
        self.size = size
        self.kenburns = kenburns
        self.reverse = index % 2 == 1  # 奇数番目はズームアウト(変化をつける)
        W, H = size
        self.overlay = make_overlay(spec.caption, size, spec.font_path, font_pct, pos_pct,
                                    text_color=spec.text_color)
        if kenburns:
            m = config.KB_MARGIN
            self.big = fit_canvas(spec.path, (int(W * m), int(H * m)))
        else:
            base = fit_canvas(spec.path, size)
            if self.overlay is not None:
                base.paste(self.overlay, (0, 0), self.overlay)
            self.static = base

    def frame(self, r):
        if not self.kenburns:
            return self.static
        r = min(1.0, max(0.0, r))
        z = 1.0 + config.KB_ZOOM * ((1 - r) if self.reverse else r)
        BW, BH = self.big.size
        cw, ch = BW / z, BH / z
        box = ((BW - cw) / 2, (BH - ch) / 2, (BW + cw) / 2, (BH + ch) / 2)
        f = self.big.resize(self.size, Image.BICUBIC, box=box)
        if self.overlay is not None:
            f.paste(self.overlay, (0, 0), self.overlay)  # 文字はズームせず固定
        return f
