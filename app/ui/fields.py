"""入力用の部品: フォント選択 (FontField) と 文字色の選択 (ColorField)。

どちらも tk の変数(StringVar)とつながっていて、変数が変わると表示も変わります。
set_enabled(False) で、押せない状態にできます。
"""
import tkinter as tk
from tkinter import colorchooser, filedialog, ttk

from .. import config
from ..core.fonts import available_fonts, font_label
from ..core.render import is_hex_color
from .widgets import FlowFrame


class FontField(ttk.Frame):
    """フォントを、一覧から選ぶ(または「ファイルから選ぶ」)部品。値はフォントファイルのパス。"""

    def __init__(self, parent, variable):
        super().__init__(parent)
        self.var = variable
        self.fonts = available_fonts()
        self.label_var = tk.StringVar(master=self, value="")
        self.columnconfigure(0, weight=1)

        self.combo = ttk.Combobox(self, textvariable=self.label_var, state="readonly", width=24,
                                  values=[label for label, _ in self.fonts])
        self.combo.grid(row=0, column=0, sticky="ew")
        self.btn = ttk.Button(self, text="ファイルから選ぶ", command=self._pick_file)
        self.btn.grid(row=0, column=1, padx=(6, 0))

        self.combo.bind("<<ComboboxSelected>>", self._on_select)
        variable.trace_add("write", lambda *a: self._sync())
        self._sync()

    def _sync(self):
        path = self.var.get().strip()
        match = next((label for label, p in self.fonts if p == path), None)
        self.label_var.set(match or font_label(path))

    def _on_select(self, _e=None):
        label = self.label_var.get()
        for lb, p in self.fonts:
            if lb == label:
                self.var.set(p)
                return

    def _pick_file(self):
        p = filedialog.askopenfilename(parent=self.winfo_toplevel(),
                                       title="フォントファイルを選んでください",
                                       filetypes=config.FONT_FILETYPES)
        if p:
            self.var.set(p)

    def set_enabled(self, enabled):
        self.combo.config(state="readonly" if enabled else "disabled")
        self.btn.config(state="normal" if enabled else "disabled")


class ColorField(FlowFrame):
    """文字の色を、ワンクリックの候補か「自由に選ぶ」で決める部品。値は '#rrggbb'。"""

    def __init__(self, parent, variable, presets=None):
        super().__init__(parent)
        self.var = variable
        self._enabled = True
        self.swatches = []
        for name, hexcolor in (presets if presets is not None else config.TEXT_COLOR_PRESETS):
            sw = tk.Label(self, text="", width=3, bg=hexcolor, relief="solid", bd=1,
                          cursor="hand2")
            sw.bind("<Button-1>", lambda e, h=hexcolor: self._choose(h))
            self.add(sw)
            self.swatches.append(sw)
        self.pick_btn = self.add(ttk.Button(self, text="自由に選ぶ", command=self._pick))
        self.cur = self.add(tk.Label(self, text="  いまの色  ", relief="solid", bd=2))
        variable.trace_add("write", lambda *a: self._sync())
        self._sync()

    def _sync(self):
        c = self.var.get().strip()
        if is_hex_color(c):
            c = c if c.startswith("#") else "#" + c
            self.cur.config(bg=c, fg="#000000" if self._light(c) else "#ffffff")

    @staticmethod
    def _light(c):
        v = c.lstrip("#")
        if len(v) == 3:
            v = "".join(ch * 2 for ch in v)
        r, g, b = int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)
        return (0.299 * r + 0.587 * g + 0.114 * b) > 140

    def _choose(self, hexcolor):
        if self._enabled:
            self.var.set(hexcolor)

    def _pick(self):
        if not self._enabled:
            return
        _rgb, hexcolor = colorchooser.askcolor(color=self.var.get(), parent=self.winfo_toplevel(),
                                               title="文字の色を選んでください")
        if hexcolor:
            self.var.set(hexcolor)

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.pick_btn.config(state="normal" if enabled else "disabled")
        for sw in self.swatches:
            sw.config(cursor="hand2" if enabled else "arrow")
        self.cur.config(relief="solid" if enabled else "flat")
