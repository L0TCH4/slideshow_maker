"""ステップを1つずつ表示する枠(上: 見出しバー / 中: 現在のステップ / 下: 戻る・次へ)。"""
from tkinter import ttk

from .. import config
from .widgets import WrapLabel


class Wizard(ttk.Frame):
    def __init__(self, parent, ctx, step_classes):
        super().__init__(parent)
        self.ctx = ctx
        self.step_classes = list(step_classes)
        self.steps = [None] * len(self.step_classes)   # 最初に開くときに作る
        self.index = None

        self._build_header()
        self._build_footer()
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

    # ---------- 上: 見出しバー
    def _build_header(self):
        h = ttk.Frame(self, style="Header.TFrame", padding=(14, 8))
        h.pack(side="top", fill="x")
        h.columnconfigure(0, weight=1)

        self.step_lbl = ttk.Label(h, style="HeaderStep.TLabel")
        self.step_lbl.grid(row=0, column=0, sticky="w")

        zoom = ttk.Frame(h, style="Header.TFrame")
        zoom.grid(row=0, column=1, sticky="ne")
        ttk.Label(zoom, text="文字", style="Header.TLabel").pack(side="left", padx=(0, 4))
        ttk.Button(zoom, text="小", width=3, style="Small.TButton",
                   command=lambda: self.ctx.change_font(-1)).pack(side="left", padx=1)
        ttk.Button(zoom, text="大", width=3, style="Small.TButton",
                   command=lambda: self.ctx.change_font(+1)).pack(side="left", padx=1)

        self.title_lbl = WrapLabel(h, style="HeaderTitle.TLabel")
        self.title_lbl.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.desc_lbl = WrapLabel(h, style="HeaderHint.TLabel")
        self.desc_lbl.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(2, 6))
        self.progress = ttk.Progressbar(h, maximum=max(1, len(self.step_classes)),
                                        mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew")

        # ウィンドウの高さが低いときは、説明文を隠して作業スペースを広げる
        self._compact = False
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, e):
        compact = e.height < config.COMPACT_HEIGHT
        if compact != self._compact:
            self._compact = compact
            if compact:
                self.desc_lbl.grid_remove()
            else:
                self.desc_lbl.grid()

    # ---------- 下: ボタン
    def _build_footer(self):
        f = ttk.Frame(self, padding=(12, 8))
        f.pack(side="bottom", fill="x")
        ttk.Separator(self, orient="horizontal").pack(side="bottom", fill="x")
        self.back_btn = ttk.Button(f, text="← 戻る", command=self.back)
        self.back_btn.pack(side="left")
        self.next_btn = ttk.Button(f, text="次へ →", style="Big.Primary.TButton", command=self.next)
        self.next_btn.pack(side="right")

    # ---------- ステップの切り替え
    def _get(self, i):
        if self.steps[i] is None:
            self.steps[i] = self.step_classes[i](self.container, self.ctx)
        return self.steps[i]

    @property
    def current(self):
        return self.steps[self.index] if self.index is not None else None

    def show(self, i):
        i = max(0, min(len(self.step_classes) - 1, i))
        if self.current is not None:
            self.current.on_hide()
            self.current.grid_forget()
        self.index = i
        step = self._get(i)
        step.grid(row=0, column=0, sticky="nsew")

        n = len(self.step_classes)
        self.step_lbl.config(text=f"ステップ {i + 1} / {n}")
        self.title_lbl.config(text=step.title)
        self.desc_lbl.config(text=step.description)
        self.progress["value"] = i + 1

        self.back_btn.config(state="normal" if i > 0 else "disabled")
        if step.show_next and i < n - 1:
            self.next_btn.config(text=step.next_label)
            self.next_btn.pack(side="right")
        else:
            self.next_btn.pack_forget()
        step.on_show()

    def next(self):
        step = self.current
        if step is None or not step.can_go_next():
            return
        if self.index < len(self.step_classes) - 1:
            self.show(self.index + 1)

    def back(self):
        if self.index and self.index > 0:
            self.show(self.index - 1)

    def set_nav_enabled(self, enabled):
        """時間のかかる処理中などに、戻る・次へを押せなくする。"""
        s = "normal" if enabled else "disabled"
        self.next_btn.config(state=s)
        self.back_btn.config(state=s if (self.index or 0) > 0 else "disabled")
