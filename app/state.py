"""アプリ全体で共有するデータ(写真・文章・設定値)。画面の各ステップはここを読み書きします。"""
import json
import os
import tkinter as tk
from dataclasses import dataclass

from . import config, session_store, settings_store
from .core.render import SlideSpec, is_hex_color
from .core.video import ExportParams


@dataclass
class Photo:
    path: str
    caption: str = ""
    # ---- 「この写真だけ変える」設定(空・None なら、全体の設定を使う)
    duration: float = None      # 表示する秒数
    font_path: str = ""         # テロップのフォント
    text_color: str = ""        # テロップの文字の色 (#RRGGBB)

    def has_override(self):
        return self.duration is not None or bool(self.font_path) or bool(self.text_color)

    def clear_override(self):
        self.duration, self.font_path, self.text_color = None, "", ""


def get_float(var, default):
    try:
        return float(var.get())
    except (tk.TclError, ValueError):
        return default


def get_int(var, default):
    try:
        return int(var.get())
    except (tk.TclError, ValueError):
        return default


class AppState:
    # 自動保存・リセットの対象になる設定値(名前は下の self.○○ の変数と同じ)
    SETTING_KEYS = ("shape", "duration", "fade", "fps", "kenburns", "telop_pos", "telop_size",
                    "telop_len", "extra_request", "audio_path", "font_path", "text_color")

    def __init__(self, root, prefs=None):
        self.prefs = prefs if prefs is not None else settings_store.load()

        # ---- データ
        self.photos = []            # list[Photo]
        self.source_text = ""       # 「伝えたい文章」
        self.ai_done = False        # テロップを作った(または文字なしで進むと決めた)か
        self.restore_note = ""      # 前回の続きを読み込んだときの案内(ステップ1に出す)
        self._last_saved = None

        # ---- 設定値(画面の入力欄とつながっている)
        v = dict(master=root)
        self.shape = tk.StringVar(**v)
        self.duration = tk.DoubleVar(**v)
        self.fade = tk.DoubleVar(**v)
        self.fps = tk.IntVar(**v)
        self.kenburns = tk.BooleanVar(**v)
        self.telop_pos = tk.DoubleVar(**v)
        self.telop_size = tk.DoubleVar(**v)
        self.telop_len = tk.IntVar(**v)
        self.extra_request = tk.StringVar(**v)
        self.audio_path = tk.StringVar(**v)
        self.font_path = tk.StringVar(**v)
        self.text_color = tk.StringVar(**v)
        self._apply_settings(self.default_settings())

        # ---- APIキー・モデル名は「作業内容」ではなく「設定」なので、リセットしても残る
        self.api_key = tk.StringVar(
            value=self.prefs.get("api_key") or os.environ.get("GEMINI_API_KEY", ""), **v)
        self.save_key = tk.BooleanVar(value=bool(self.prefs.get("api_key")), **v)
        self.model = tk.StringVar(
            value=self.prefs.get("model") or config.GEMINI["model"], **v)

    # ================================================ 設定値
    @staticmethod
    def default_settings():
        d = config.DEFAULTS
        return {
            "shape": d["shape"], "duration": d["duration"], "fade": d["fade"], "fps": d["fps"],
            "kenburns": d["kenburns"], "telop_pos": d["telop_pos"], "telop_size": d["telop_size"],
            "telop_len": d["telop_len"], "extra_request": "", "audio_path": "",
            "font_path": config.find_default_font(), "text_color": d["text_color"],
        }

    def _apply_settings(self, values):
        defaults = self.default_settings()
        for key in self.SETTING_KEYS:
            val = values.get(key, defaults[key])
            if key == "shape" and val not in config.SHAPES:
                val = defaults[key]
            if key == "audio_path" and val and not os.path.isfile(val):
                val = ""
            try:
                getattr(self, key).set(val)
            except (tk.TclError, ValueError, TypeError):
                getattr(self, key).set(defaults[key])

    def _current_settings(self):
        d = self.default_settings()
        return {
            "shape": self.shape.get(),
            "duration": get_float(self.duration, d["duration"]),
            "fade": get_float(self.fade, d["fade"]),
            "fps": get_int(self.fps, d["fps"]),
            "kenburns": bool(self.kenburns.get()),
            "telop_pos": get_float(self.telop_pos, d["telop_pos"]),
            "telop_size": get_float(self.telop_size, d["telop_size"]),
            "telop_len": get_int(self.telop_len, d["telop_len"]),
            "extra_request": self.extra_request.get(),
            "audio_path": self.audio_path.get(),
            "font_path": self.font_path.get(),
            "text_color": self.text_color.get(),
        }

    # ================================================ 自動保存・復元・リセット
    def to_session(self):
        return {
            "version": session_store.VERSION,
            "photos": [{"path": p.path, "caption": p.caption, "duration": p.duration,
                        "font_path": p.font_path, "text_color": p.text_color}
                       for p in self.photos],
            "source_text": self.source_text,
            "ai_done": self.ai_done,
            "settings": self._current_settings(),
        }

    def load_session(self, data):
        """前回の作業内容を読み込む。見つからなくなった写真は除き、restore_note に案内を入れる。"""
        if not data:
            return
        photos, missing = [], 0
        for item in data.get("photos", []):
            path = item.get("path", "")
            if not os.path.isfile(path):
                missing += 1
                continue
            dur = item.get("duration")
            photos.append(Photo(path=path, caption=item.get("caption", ""),
                                duration=float(dur) if dur is not None else None,
                                font_path=item.get("font_path", ""),
                                text_color=item.get("text_color", "")))
        self.photos = photos
        self.source_text = data.get("source_text", "")
        self.ai_done = bool(data.get("ai_done", False)) and bool(photos)
        self._apply_settings(data.get("settings", {}))
        self._last_saved = json.dumps(self.to_session(), sort_keys=True, ensure_ascii=False)

        if photos or self.source_text.strip():
            note = f"前回の続きから始めています(写真 {len(photos)} 枚)。"
            if missing:
                note += f"\n※ 見つからなくなった写真 {missing} 枚は除きました。"
            self.restore_note = note

    def autosave(self, force=False):
        """変更があったときだけ、作業内容をファイルに保存する。"""
        if not config.AUTOSAVE_ENABLED:
            return
        data = self.to_session()
        text = json.dumps(data, sort_keys=True, ensure_ascii=False)
        if force or text != self._last_saved:
            session_store.save(data)
            self._last_saved = text

    def reset_all(self):
        """写真・文章・テロップ・動画の設定を、すべて最初の状態に戻す。(APIキーは残す)"""
        self.photos = []
        self.source_text = ""
        self.ai_done = False
        self.restore_note = ""
        self._apply_settings(self.default_settings())
        if config.AUTOSAVE_ENABLED:
            session_store.clear()
            self._last_saved = None

    def reset(self):
        """写真と文章だけを消す(設定はそのまま)。"""
        self.photos = []
        self.source_text = ""
        self.ai_done = False

    # ================================================ 便利メソッド
    def shape_size(self):
        return config.SHAPES.get(self.shape.get()) or next(iter(config.SHAPES.values()))

    def has_captions(self):
        return any(p.caption.strip() for p in self.photos)

    # ---- 写真ごとの設定(個別設定があればそれ、なければ全体の設定)
    def duration_for_default(self):
        return get_float(self.duration, config.DEFAULTS["duration"])

    def duration_for(self, photo):
        if photo.duration is not None:
            return photo.duration
        return self.duration_for_default()

    def font_for(self, photo):
        return (photo.font_path or self.font_path.get()).strip()

    def color_for(self, photo):
        for c in (photo.text_color, self.text_color.get()):
            if is_hex_color(c or ""):
                return c.strip()
        return config.DEFAULTS["text_color"]

    def total_seconds(self):
        from .core.video import total_seconds
        return total_seconds([self.duration_for(p) for p in self.photos],
                             get_float(self.fade, config.DEFAULTS["fade"]))

    def save_prefs(self):
        """次回も使いたい「設定」を保存する(APIキーは「保存する」にチェックがあるときだけ)。"""
        self.prefs["model"] = self.model.get().strip() or config.GEMINI["model"]
        if self.save_key.get() and self.api_key.get().strip():
            self.prefs["api_key"] = self.api_key.get().strip()
        else:
            self.prefs.pop("api_key", None)
        settings_store.save(self.prefs)

    def export_params(self, out_path):
        specs = [SlideSpec(path=p.path, caption=p.caption, duration=self.duration_for(p),
                           font_path=self.font_for(p), text_color=self.color_for(p))
                 for p in self.photos]
        return ExportParams(
            photos=specs,
            out_path=out_path,
            size=self.shape_size(),
            fade=get_float(self.fade, config.DEFAULTS["fade"]),
            fps=get_int(self.fps, config.DEFAULTS["fps"]),
            kenburns=bool(self.kenburns.get()),
            font_pct=get_float(self.telop_size, config.DEFAULTS["telop_size"]),
            pos_pct=get_float(self.telop_pos, config.DEFAULTS["telop_pos"]),
            audio_path=self.audio_path.get().strip(),
        )
