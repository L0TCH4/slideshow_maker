"""アプリの起動処理: ウィンドウ → フォント/スタイル → 状態(前回の続き) → ウィザード。"""
from .. import config, session_store, settings_store
from ..state import AppState
from . import dnd
from .context import AppContext
from .steps import STEP_CLASSES
from .style import Fonts, setup_style
from .wizard import Wizard


def create_app(root):
    """ウィンドウ root の中にアプリを組み立てて、(state, ctx, wizard, 保存する関数) を返す。"""
    prefs = settings_store.load()
    fonts = Fonts(root, prefs.get("ui_font_size", config.UI_FONT_SIZE))
    setup_style(root, fonts)

    state = AppState(root, prefs)
    if config.AUTOSAVE_ENABLED:
        state.load_session(session_store.load())      # 前回の作業内容を読み込む

    ctx = AppContext(root, state, fonts)
    wizard = Wizard(root, ctx, STEP_CLASSES)
    ctx.wizard = wizard
    wizard.pack(fill="both", expand=True)
    wizard.show(0)                                    # 前回の続きでも、必ずステップ1から

    def save_now(force=False):
        """入力途中の内容を state に取り込んでから、自動保存する。"""
        if wizard.current is not None:
            wizard.current.flush()
        state.autosave(force=force)

    def tick():
        try:
            save_now()
        finally:
            root.after(config.AUTOSAVE_INTERVAL_MS, tick)

    if config.AUTOSAVE_ENABLED:
        root.after(config.AUTOSAVE_INTERVAL_MS, tick)
    return state, ctx, wizard, save_now


def run():
    root = dnd.create_root()
    root.title(config.APP_TITLE)

    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w = min(config.WINDOW_DEFAULT_SIZE[0], sw - 40)
    h = min(config.WINDOW_DEFAULT_SIZE[1], sh - 80)
    root.geometry(f"{w}x{h}+20+20")
    root.minsize(*config.WINDOW_MIN_SIZE)

    state, ctx, wizard, save_now = create_app(root)

    # キーボードで文字サイズを変える: Ctrl + (+ / - / 0)
    for seq in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
        root.bind(seq, lambda e: ctx.change_font(+1))
    for seq in ("<Control-minus>", "<Control-KP_Subtract>"):
        root.bind(seq, lambda e: ctx.change_font(-1))
    root.bind("<Control-0>", lambda e: ctx.reset_font())

    def on_close():
        try:
            if config.AUTOSAVE_ENABLED:
                save_now(force=True)
            state.save_prefs()
        finally:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
