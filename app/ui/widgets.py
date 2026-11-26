"""ウィンドウの大きさに合わせて変わる、再利用できる部品たち。

- ScrollFrame        : 中身が入りきらないとき、自動でスクロールできる枠
- WrapLabel          : 幅に合わせて自動で折り返す文字
- FlowFrame          : ボタンなどを並べ、幅が足りなければ次の行へ回す枠
- ResponsiveColumns  : 広いときは左右2列、狭いときは上下に並ぶ枠
- PreviewPane        : 枠の大きさに合わせて絵を描き直すプレビュー
"""
import tkinter as tk
from tkinter import ttk

from .. import config


class ScrollFrame(ttk.Frame):
    """縦にスクロールできる枠。部品は `.inner` に置く。
    ウィンドウが大きいときは中身が枠いっぱいに広がり、小さいときはスクロールになる。"""

    def __init__(self, parent, padding=12):
        super().__init__(parent)
        bg = ttk.Style().lookup("TFrame", "background") or self.winfo_toplevel().cget("bg")
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, background=bg)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.inner = ttk.Frame(self.canvas, padding=padding)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._bar_visible = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.inner.bind("<Configure>", lambda e: self._relayout())
        self.canvas.bind("<Configure>", lambda e: self._relayout())
        self.bind("<Enter>", self._bind_wheel)
        self.bind("<Leave>", self._unbind_wheel)
        self._last_rh = -1
        self.after(150, self._watch)

    def _watch(self):
        """中身が必要とする高さが変わったことは <Configure> では気づけないので、定期的に確かめる。"""
        try:
            if self.inner.winfo_reqheight() != self._last_rh:
                self._relayout()
            self.after(150, self._watch)
        except tk.TclError:
            pass                                    # ウィンドウが閉じられた

    def _relayout(self):
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        rh = self.inner.winfo_reqheight()
        self._last_rh = rh
        h = max(ch, rh)
        self.canvas.itemconfigure(self._win, width=cw, height=h)
        self.canvas.configure(scrollregion=(0, 0, cw, h))
        need = rh > ch + 1
        if need and not self._bar_visible:
            self.vbar.grid(row=0, column=1, sticky="ns")
            self._bar_visible = True
        elif not need and self._bar_visible:
            self.vbar.grid_remove()
            self._bar_visible = False
            self.canvas.yview_moveto(0)

    # ---- マウスホイール
    def _bind_wheel(self, _e):
        self.canvas.bind_all("<MouseWheel>", self._wheel)
        self.canvas.bind_all("<Button-4>", self._wheel)
        self.canvas.bind_all("<Button-5>", self._wheel)

    def _unbind_wheel(self, _e):
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(seq)

    def _wheel(self, e):
        if not self._bar_visible:
            return
        if e.widget.winfo_class() in ("Text", "Listbox", "TCombobox"):
            return                                  # それらは自分でスクロールする
        up = e.num == 4 or getattr(e, "delta", 0) > 0
        self.canvas.yview_scroll(-3 if up else 3, "units")


class WrapLabel(ttk.Label):
    """置かれた幅に合わせて、自動で折り返すラベル。"""

    def __init__(self, parent, **kw):
        kw.setdefault("wraplength", 300)
        super().__init__(parent, **kw)
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, e):
        w = max(100, e.width - 4)
        if int(float(self.cget("wraplength"))) != w:
            self.configure(wraplength=w)


class FlowFrame(ttk.Frame):
    """部品を左から順に並べ、幅が足りなければ次の行に回す枠。"""

    def __init__(self, parent, pad=4):
        super().__init__(parent)
        self._items = []
        self._pad = pad
        self._width = 0
        self.bind("<Configure>", self._on_configure)

    def add(self, widget):
        self._items.append(widget)
        self._layout()
        return widget

    def _on_configure(self, e):
        if e.width != self._width:
            self._width = e.width
            self._layout()

    def _layout(self):
        width = self._width or 10 ** 6
        x = row = col = 0
        for w in self._items:
            rw = w.winfo_reqwidth() + self._pad
            if col > 0 and x + rw > width:
                row += 1
                col = x = 0
            w.grid(row=row, column=col, padx=(0, self._pad), pady=self._pad // 2, sticky="w")
            x += rw
            col += 1


class ResponsiveColumns(ttk.Frame):
    """広いときは左右2列、狭いときは上下に並べる枠。中身は .left / .right に置く。"""

    def __init__(self, parent, breakpoint=None, left_weight=1, right_weight=1):
        super().__init__(parent)
        self.left = ttk.Frame(self)
        self.right = ttk.Frame(self)
        self._bp = breakpoint or config.LAYOUT_BREAKPOINT
        self._weights = (left_weight, right_weight)
        self._mode = None
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, e):
        mode = "wide" if e.width >= self._bp else "narrow"
        if mode == self._mode:
            return
        self._mode = mode
        for w in (self.left, self.right):
            w.grid_forget()
        for i in range(2):
            self.columnconfigure(i, weight=0, uniform="")
            self.rowconfigure(i, weight=0)
        if mode == "wide":
            self.rowconfigure(0, weight=1)
            self.columnconfigure(0, weight=self._weights[0], uniform="cols")
            self.columnconfigure(1, weight=self._weights[1], uniform="cols")
            self.left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            self.right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        else:
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            self.left.grid(row=0, column=0, sticky="nsew")
            self.right.grid(row=1, column=0, sticky="nsew", pady=(10, 0))


class PreviewPane(tk.Frame):
    """枠の大きさに合わせて絵を描き直すプレビュー。

    render_fn(幅, 高さ) が PIL 画像(なければ None)を返す。
    ウィンドウの大きさが変わったり refresh() を呼ぶと、描き直される。
    """

    def __init__(self, parent, render_fn, min_size=(240, 160), placeholder=""):
        from PIL import ImageTk
        self._ImageTk = ImageTk
        c = config.COLORS
        super().__init__(parent, bg=c["preview_bg"], width=min_size[0], height=min_size[1])
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._render_fn = render_fn
        self.placeholder = placeholder
        self._photo = None
        self._job = None
        self.label = tk.Label(self, bg=c["preview_bg"], fg=c["preview_fg"], justify="center",
                              font="TkDefaultFont")
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        self.bind("<Configure>", lambda e: self.refresh())

    def refresh(self):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(40, self._draw)

    def _draw(self):
        self._job = None
        w, h = self.winfo_width(), self.winfo_height()
        if w < 30 or h < 30:
            return
        try:
            img = self._render_fn(w - 8, h - 8)
        except Exception as e:
            img = None
            print(f"プレビューを描けませんでした: {e}")
        if img is None:
            self._photo = None
            self.label.config(image="", text=self.placeholder, wraplength=max(100, w - 30))
        else:
            self._photo = self._ImageTk.PhotoImage(img)
            self.label.config(image=self._photo, text="")
