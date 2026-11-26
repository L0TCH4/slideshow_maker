"""ステップ3: AIに考えてもらう(文章 → 全部の写真ぶんのテロップ)"""
import tkinter as tk
from tkinter import ttk

from ...core import gemini
from ...state import get_int
from ..background import run_async
from ..widgets import FlowFrame, WrapLabel
from .base import Step


class AIGenerateStep(Step):
    title = "AIに考えてもらう"
    description = "ボタンを押すと、AIが文章を読んで、全部の写真ぶんのテロップをまとめて作ります。"

    def build(self, body):
        self._busy = False
        self._adv_open = False

        self.summary = WrapLabel(body)
        self.summary.grid(row=0, column=0, sticky="ew")

        # ---- APIキー
        key_box = ttk.LabelFrame(body, text=" Gemini の APIキー ", padding=8)
        key_box.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        key_box.columnconfigure(0, weight=1)
        self.key_entry = ttk.Entry(key_box, textvariable=self.state.api_key, show="*")
        self.key_entry.grid(row=0, column=0, sticky="ew")
        self.show_key = tk.BooleanVar(master=self.winfo_toplevel(), value=False)
        ttk.Checkbutton(key_box, text="表示する", variable=self.show_key,
                        command=self._toggle_show).grid(row=0, column=1, padx=(8, 0))
        ttk.Checkbutton(key_box, text="このパソコンに保存する(次回から入力不要)",
                        variable=self.state.save_key).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        WrapLabel(key_box, style="Hint.TLabel",
                  text="APIキーは「Google AI Studio」(aistudio.google.com)で無料で作れます。"
                       "他の人に見せないよう注意してください。\n"
                       "入力した文章は、AIで処理するためGoogleのサーバーに送られます(写真は送りません)。"
                  ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.adv_btn = ttk.Button(key_box, text="▶ くわしい設定", style="Small.TButton",
                                  command=self._toggle_adv)
        self.adv_btn.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.adv = ttk.Frame(key_box)
        ttk.Label(self.adv, text="AIモデル名").pack(side="left")
        ttk.Entry(self.adv, textvariable=self.state.model, width=26).pack(side="left", padx=8)

        # ---- 実行
        run = FlowFrame(body)
        run.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        self.run_btn = run.add(ttk.Button(run, text="AIに考えてもらう", style="Big.Primary.TButton",
                                          command=self.run))
        self.skip_btn = run.add(ttk.Button(run, text="AIを使わずに進む(文字なし)",
                                           command=self.skip))

        self.bar = ttk.Progressbar(body, mode="indeterminate")
        self.status = WrapLabel(body)
        self.status.grid(row=4, column=0, sticky="ew", pady=(6, 0))

    # ---------- 表示
    def on_show(self):
        n, m = len(self.state.photos), len(self.state.source_text.strip())
        self.summary.config(
            text=f"写真 {n} 枚 / 文章 {m} 文字 → AIが {n} 個のテロップを作ります。")
        self.run_btn.config(text="もう一度AIに考えてもらう" if self.state.ai_done
                            else "AIに考えてもらう")
        if self.state.ai_done:
            self.status.config(text="前回の結果が残っています。このまま「次へ」で確認できます。")
        elif not self._busy:
            self.status.config(text="準備ができたら、上のボタンを押してください。")

    def _toggle_show(self):
        self.key_entry.config(show="" if self.show_key.get() else "*")

    def _toggle_adv(self):
        self._adv_open = not self._adv_open
        if self._adv_open:
            self.adv.grid(row=4, column=0, sticky="w", pady=(4, 0))
            self.adv_btn.config(text="▼ くわしい設定")
        else:
            self.adv.grid_forget()
            self.adv_btn.config(text="▶ くわしい設定")

    # ---------- AIを呼ぶ
    def run(self):
        if self._busy:
            return
        s = self.state
        text = s.source_text.strip()
        key = s.api_key.get().strip()
        if not text:
            self.info("文章がありません。前の画面に戻って、伝えたい文章を書いてください。")
            return
        if not key:
            self.info("GeminiのAPIキーを入れてください。")
            return
        if s.has_captions() and not self.confirm(
                "すでに入っているテロップは、AIの結果で上書きされます。\nよろしいですか?"):
            return

        s.save_prefs()
        count = len(s.photos)
        length = max(1, get_int(s.telop_len, 25))
        model = s.model.get().strip()
        extra = s.extra_request.get()

        self._set_busy(True)
        self.status.config(text="AIが考えています…(10〜30秒かかることがあります)")
        run_async(self,
                  lambda progress: gemini.generate_telops(key, model, text, count, length, extra),
                  self._on_ok, self._on_error)

    def _on_ok(self, result):
        telops, note = result
        for photo, cap in zip(self.state.photos, telops):
            photo.caption = cap
        self.state.ai_done = True
        self._set_busy(False)
        self.status.config(text="できました!次の画面で内容を確認します。" + (f"\n({note})" if note else ""))
        self.after(800, self.ctx.wizard.next)

    def _on_error(self, err):
        self._set_busy(False)
        self.status.config(text="うまくいきませんでした。")
        self.error(str(err))

    def skip(self):
        if self._busy:
            return
        if self.confirm("AIを使わずに進みます。\nテロップは文字なしになります(次の画面で自分で入力もできます)。\n"
                        "よろしいですか?"):
            for p in self.state.photos:
                p.caption = ""
            self.state.ai_done = True
            self.ctx.wizard.next()

    def _set_busy(self, busy):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.run_btn.config(state=state)
        self.skip_btn.config(state=state)
        self.ctx.wizard.set_nav_enabled(not busy)
        if busy:
            self.bar.grid(row=3, column=0, sticky="ew", pady=(10, 0))
            self.bar.start(12)
        else:
            self.bar.stop()
            self.bar.grid_remove()

    def can_go_next(self):
        if self._busy:
            return False
        if not self.state.ai_done:
            if not self.confirm("まだAIに考えてもらっていません。\n文字なしで進みますか?\n"
                                "(次の画面で、自分でテロップを入力することもできます)"):
                return False
            self.state.ai_done = True
        return True
