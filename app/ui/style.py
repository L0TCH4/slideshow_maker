"""文字の大きさ・色・ボタンの見た目をまとめて設定する。"""
import tkinter.font as tkfont
from tkinter import TclError, ttk

from .. import config


class Fonts:
    """基本フォントと、見出し用などの派生フォント。apply() で全部いっぺんに大きさを変えられる。"""
    NAMED = ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
             "TkCaptionFont", "TkTooltipFont")

    def __init__(self, root, size):
        base = tkfont.nametofont("TkDefaultFont")
        self.title = base.copy()
        self.step = base.copy()
        self.big = base.copy()
        self.hint = base.copy()
        self.size = size
        self.apply(size)

    def apply(self, size):
        lo, hi = config.UI_FONT_RANGE
        self.size = size = max(lo, min(hi, int(size)))
        for name in self.NAMED:
            try:
                f = tkfont.nametofont(name)
                f.configure(size=size)
                if config.UI_FONT_FAMILY:
                    f.configure(family=config.UI_FONT_FAMILY)
            except TclError:
                pass
        d = config.UI_FONT_DELTAS
        for font, key, bold in ((self.title, "title", True), (self.step, "step", True),
                                (self.big, "big", True), (self.hint, "hint", False)):
            font.configure(size=max(7, size + d[key]), weight="bold" if bold else "normal")
            if config.UI_FONT_FAMILY:
                font.configure(family=config.UI_FONT_FAMILY)


def setup_style(root, fonts):
    c = config.COLORS
    style = ttk.Style(root)
    try:
        style.theme_use(config.THEME)
    except TclError:
        pass
    root.option_add("*TCombobox*Listbox.font", tkfont.nametofont("TkDefaultFont"))

    style.configure("TButton", padding=(12, 8))
    style.configure("Primary.TButton", background=c["accent"], foreground=c["accent_text"])
    style.map("Primary.TButton",
              background=[("disabled", c["accent_disabled"]), ("active", c["accent_active"])],
              foreground=[("disabled", "#f0f0f0")])
    style.configure("Big.Primary.TButton", font=fonts.big, padding=(18, 14))
    style.configure("Big.TButton", font=fonts.big, padding=(18, 14))

    style.configure("TLabelframe.Label", font=fonts.step, foreground=c["accent"])
    style.configure("TCheckbutton", padding=6)
    style.configure("TRadiobutton", padding=4)
    style.configure("Hint.TLabel", font=fonts.hint, foreground=c["hint"])
    style.configure("TProgressbar", thickness=16, background=c["accent"])

    style.configure("Header.TFrame", background=c["header_bg"])
    style.configure("Header.TLabel", background=c["header_bg"])
    style.configure("HeaderStep.TLabel", background=c["header_bg"], foreground=c["accent"],
                    font=fonts.step)
    style.configure("HeaderTitle.TLabel", background=c["header_bg"], font=fonts.title)
    style.configure("HeaderHint.TLabel", background=c["header_bg"], foreground=c["hint"])
    style.configure("Small.TButton", padding=(8, 2))
    style.configure("Danger.TButton", foreground=c["error"])
    return style
