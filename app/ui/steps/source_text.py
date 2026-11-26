"""ステップ2: 伝えたい文章を書く(全部の写真ぶんをまとめて1つ書く)"""
import tkinter as tk
from tkinter import ttk

from ... import config
from ..widgets import WrapLabel
from .base import Step


class SourceTextStep(Step):
    title = "伝えたい文章を書く"
    description = ("動画で伝えたいことを、ふつうの文章で書いてください。"
                   "次の画面で、AIが写真の枚数に合わせて短いテロップに分けます。")

    def build(self, body):
        body.rowconfigure(1, weight=1)

        self.count_lbl = WrapLabel(body)
        self.count_lbl.grid(row=0, column=0, sticky="ew")

        box = ttk.Frame(body)
        box.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        self.text = tk.Text(box, height=9, wrap="word", font="TkDefaultFont", undo=True)
        sb = ttk.Scrollbar(box, command=self.text.yview)
        self.text.config(yscrollcommand=sb.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.text.insert("1.0", self.state.source_text)
        self.text.bind("<KeyRelease>", lambda e: self._update_counter())

        self.len_lbl = WrapLabel(body, style="Hint.TLabel")
        self.len_lbl.grid(row=2, column=0, sticky="ew", pady=(4, 0))

        opt = ttk.LabelFrame(body, text=" くわしい指定(そのままでもOK) ", padding=8)
        opt.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        opt.columnconfigure(1, weight=1)

        ttk.Label(opt, text="テロップ1つの長さ").grid(row=0, column=0, sticky="w")
        f = ttk.Frame(opt)
        f.grid(row=0, column=1, sticky="w", padx=(8, 0))
        lo, hi = config.TELOP_LENGTH_RANGE
        ttk.Spinbox(f, from_=lo, to=hi, increment=5, width=5,
                    textvariable=self.state.telop_len).pack(side="left")
        ttk.Label(f, text="文字くらい").pack(side="left", padx=6)

        ttk.Label(opt, text="AIへのお願い").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(opt, textvariable=self.state.extra_request).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        WrapLabel(opt, style="Hint.TLabel",
                  text="例: やさしい口調で / です・ます調で / 楽しい雰囲気で / 体言止めで短く").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    def on_show(self):
        n = len(self.state.photos)
        self.count_lbl.config(text=f"写真は {n} 枚です。"
                                   f"\n例: 1つ目は，ショートケーキの写真です。2つ目は，チョコケーキの写真です。3つ目は，フルーツタルトの写真です。買ってもらえるように宣伝してください。")
        self._update_counter()

    def _update_counter(self):
        n = len(self.text.get("1.0", "end-1c").strip())
        self.len_lbl.config(text=f"{n} 文字")

    def _save(self):
        self.state.source_text = self.text.get("1.0", "end-1c")

    def on_hide(self):
        self._save()

    def flush(self):
        self._save()

    def reset(self):
        """「最初からやり直す」のとき、入力欄を空にする。"""
        self.text.delete("1.0", "end")
        self._update_counter()

    def can_go_next(self):
        self._save()
        if not self.state.source_text.strip():
            self.info("伝えたい文章を書いてください。\n"
                      "短いメモでも大丈夫です。")
            return False
        return True
