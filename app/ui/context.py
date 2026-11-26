"""画面の各部分が共有する「道具箱」(ウィンドウ・状態・フォント・ウィザード)。"""
from .. import settings_store


class AppContext:
    def __init__(self, root, state, fonts):
        self.root = root
        self.state = state
        self.fonts = fonts
        self.wizard = None          # 起動時に Wizard が入る

    def change_font(self, delta):
        self.fonts.apply(self.fonts.size + delta)
        self.state.prefs["ui_font_size"] = self.fonts.size

    def reset_font(self):
        from .. import config
        self.fonts.apply(config.UI_FONT_SIZE)
        self.state.prefs["ui_font_size"] = self.fonts.size
