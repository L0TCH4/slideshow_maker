"""
★ カスタマイズの入口 ★

見た目・初期値・数値・AIの設定は、ほとんどこのファイルで変えられます。
(AIへの指示文は prompts.py、画面の順番は ui/steps/__init__.py にあります)
"""
import os

# ============================================================ アプリ全体
APP_TITLE = "スライドショー動画メーカー"
WINDOW_DEFAULT_SIZE = (1100, 780)    # 起動時のウィンドウの大きさ(幅, 高さ)
WINDOW_MIN_SIZE = (460, 400)         # これより小さくはできない
THEME = "clam"                       # 画面のテーマ ("clam", "alt", "default" など)
LAYOUT_BREAKPOINT = 860              # 幅(px)がこれより狭いと、2列の画面を縦並びに切り替える
COMPACT_HEIGHT = 560                 # 高さ(px)がこれより低いと、上部の説明文を隠して作業スペースを広げる

# ============================================================ 文字の大きさ・色
UI_FONT_FAMILY = ""                  # 例: "Meiryo UI" (空なら標準のフォント)
UI_FONT_SIZE = 14                    # 基本の文字サイズ(画面右上の A- / A+ でも変えられます)
UI_FONT_RANGE = (9, 30)              # A- / A+ で変えられる範囲
UI_FONT_DELTAS = {                   # 基本サイズからの差
    "title": 8,                      # 各画面の大見出し
    "step": 3,                       # 枠の見出し
    "big": 5,                        # 大きなボタン
    "hint": -2,                      # 小さな説明文
}
COLORS = {
    "accent": "#1a5fb4",             # メインの色(ボタン・見出し)
    "accent_active": "#15488a",
    "accent_text": "#ffffff",
    "accent_disabled": "#9aa9bd",
    "hint": "#555555",               # 説明文の色
    "header_bg": "#eef3fb",          # 上部バーの背景
    "preview_bg": "#222222",         # プレビューの背景
    "preview_fg": "#cccccc",
    "error": "#c01c28",
    "ok": "#26a269",
}

# ============================================================ 動画の形(名前: (幅, 高さ))
# 偶数にしてください。行を足す/消すと、画面の選択肢も変わります。
SHAPES = {
    "横長 (パソコン・YouTube)": (1280, 720),
    "横長 高画質 (フルHD)": (1920, 1080),
    "縦長 (スマホ・ショート動画)": (1080, 1920),
    "正方形 (Instagram)": (1080, 1080),
}

# ============================================================ 初期値
DEFAULTS = {
    "shape": "正方形 (Instagram)",   # SHAPES の名前のどれか
    "duration": 3.0,                       # 1枚の表示秒数
    "fade": 0.5,                           # 切り替え(フェード)の秒数
    "fps": 30,
    "kenburns": True,                      # ゆっくりズーム
    "telop_pos": 90.0,                     # テロップの高さ 0(上)〜100(下)
    "telop_size": 6.0,                     # テロップの文字の大きさ(画面の高さの%)
    "telop_len": 25,                       # テロップ1つの長さ(文字数のめやす)
    "text_color": "#ffffff",               # テロップの文字の色(#RRGGBB)
}

# 文字の色の「ワンクリック候補」(名前, 色)。足したり消したりできます
TEXT_COLOR_PRESETS = [
    ("白", "#ffffff"), ("黄", "#ffe600"), ("黒", "#000000"),
    ("赤", "#ff4d4d"), ("青", "#4da6ff"), ("緑", "#5fe07a"), ("ピンク", "#ff8fd0"),
]

# ============================================================ スライダー・入力欄の範囲
TELOP_SIZE_RANGE = (3, 14)
TELOP_LENGTH_RANGE = (5, 100)
DURATION_RANGE = (1, 60)
FADE_RANGE = (0, 3)
FPS_RANGE = (10, 60)

# ============================================================ テロップのデザイン
# 色は (R, G, B, 不透明度) で 0〜255。band_color の最後を 0 にすると帯なしになります。
# (文字の色そのものは、画面のステップ5で選びます。初期値は DEFAULTS["text_color"])
TELOP_STYLE = {
    "band_color": (0, 0, 0, 150),
    "stroke_color": (0, 0, 0, 255),   # 文字のフチ
    "auto_contrast": True,            # 暗い文字色のとき、帯とフチを自動で白にして読みやすくする
    "line_spacing": 1.3,              # 行の間隔(文字サイズの倍率)
    "band_padding": 0.5,              # 帯の上下の余白(文字サイズの倍率)
    "side_margin": 0.05,              # 左右の余白(画面幅の割合)
    "v_margin": 0.03,                 # 上下の余白(画面高さの割合)
}

# ============================================================ ズーム効果(Ken Burns)
KB_ZOOM = 0.12       # ズームの量 (0.12 = 12%)
KB_MARGIN = 1.2      # ズーム用に大きめに作る倍率(画質のため。KB_ZOOMより大きく)

# ============================================================ 動画の書き出し
VIDEO_ENCODE = {"crf": 20, "preset": "medium", "audio_bitrate": "192k"}
DEFAULT_FILENAME = "slideshow.mp4"

# ============================================================ AI (Gemini)
GEMINI = {
    "model": "gemini-flash-lite-latest",     # 「モデルが見つかりません」と出たら、使えるモデル名に変更
    "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    "timeout": 150,                  # 返事を待つ秒数
    "temperature": 0.4,              # 小さいほど堅実、大きいほど自由
}

# ============================================================ ファイル関連
IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"}
IMG_FILETYPES = [("画像ファイル", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff"),
                 ("すべてのファイル", "*.*")]
AUDIO_FILETYPES = [("音声", "*.mp3 *.wav *.m4a *.aac *.ogg *.flac"), ("すべて", "*.*")]
FONT_FILETYPES = [("フォント", "*.ttf *.ttc *.otf"), ("すべて", "*.*")]

# テロップに使う日本語フォントの探し場所(上にあるものほど優先)
FONT_CANDIDATES = [
    # Windows
    r"C:\Windows\Fonts\meiryob.ttc", r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothB.ttc", r"C:\Windows\Fonts\msgothic.ttc",
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]

# フォント選択の一覧に出す名前(ファイル名: 表示名)。ここにないものはファイル名がそのまま出ます
FONT_LABELS = {
    "meiryob.ttc": "メイリオ(太字)", "meiryo.ttc": "メイリオ",
    "YuGothB.ttc": "游ゴシック(太字)", "msgothic.ttc": "MS ゴシック",
    "ヒラギノ角ゴシック W6.ttc": "ヒラギノ角ゴシック",
    "Hiragino Sans GB.ttc": "Hiragino Sans GB", "AppleSDGothicNeo.ttc": "Apple SD Gothic Neo",
    "NotoSansCJK-Bold.ttc": "Noto Sans CJK(太字)", "NotoSansCJK-Regular.ttc": "Noto Sans CJK",
    "TakaoPGothic.ttf": "Takao Pゴシック",
}

# システムのフォントを全部探すときのフォルダ
FONT_DIRS = [
    # Windows
    r"C:\Windows\Fonts",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
    # macOS
    "/System/Library/Fonts", "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
    # Linux
    "/usr/share/fonts", "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"),
]
FONT_EXTENSIONS = (".ttf", ".ttc", ".otf")

# 設定(APIキーなど)を保存するファイル
USER_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".slideshow_maker.json")

# ============================================================ 自動保存(前回の続きから)
AUTOSAVE_ENABLED = True              # False にすると、保存も復元もしない
AUTOSAVE_INTERVAL_MS = 3000          # 何ミリ秒ごとに保存するか(変更があったときだけ書き込みます)
SESSION_PATH = os.path.join(os.path.expanduser("~"), ".slideshow_maker_session.json")


def find_default_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return ""
