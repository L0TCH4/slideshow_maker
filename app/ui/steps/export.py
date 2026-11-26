"""ステップ6: 動画を作る"""
import os
import subprocess
import sys
import threading
from tkinter import filedialog, ttk

from ... import config
from ...core.video import ExportCancelled, export_video
from ..background import run_async
from ..widgets import FlowFrame, WrapLabel
from .base import Step


def open_folder(path):
    """保存先のフォルダを、OSの標準のファイル画面で開く。"""
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)                       # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


class ExportStep(Step):
    title = "動画を作る"
    description = "いよいよ完成です。ボタンを押して、保存先を決めてください。"
    show_next = False

    def build(self, body):
        self._busy = False
        self._cancel = None
        self._out = ""

        box = ttk.LabelFrame(body, text=" 作る動画の内容 ", padding=10)
        box.grid(row=0, column=0, sticky="ew")
        box.columnconfigure(0, weight=1)
        self.summary = WrapLabel(box, justify="left")
        self.summary.grid(row=0, column=0, sticky="ew")

        btns = FlowFrame(body)
        btns.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        self.make_btn = btns.add(ttk.Button(btns, text="動画を作る (MP4)",
                                            style="Big.Primary.TButton", command=self.start))
        self.cancel_btn = ttk.Button(btns, text="中止する", command=self.cancel)
        self._btns = btns

        self.bar = ttk.Progressbar(body, mode="determinate", maximum=100)
        self.bar.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        self.status = WrapLabel(body)
        self.status.grid(row=3, column=0, sticky="ew", pady=(6, 0))

        self.after_box = FlowFrame(body)
        self.open_btn = ttk.Button(self.after_box, text="保存先のフォルダを開く",
                                   command=lambda: open_folder(os.path.dirname(self._out)))
        self.restart_btn = ttk.Button(self.after_box, text="最初からやり直す", command=self.restart)
        self.after_box.add(self.open_btn)
        self.after_box.add(self.restart_btn)

    def on_show(self):
        s = self.state
        sec = s.total_seconds()
        w, h = s.shape_size()
        caps = sum(1 for p in s.photos if p.caption.strip())
        audio = os.path.basename(s.audio_path.get()) or "なし"
        custom = sum(1 for p in s.photos if p.has_override())
        self.summary.config(text=(
            f"・写真: {len(s.photos)} 枚(テロップ入り {caps} 枚)\n"
            f"・動画の形: {s.shape.get()}  {w}×{h}\n"
            f"・長さ: 約 {sec:.0f} 秒    ズーム効果: {'あり' if s.kenburns.get() else 'なし'}\n"
            f"・BGM: {audio}"
            + (f"\n・写真ごとの個別設定: {custom} 枚" if custom else "")))
        if not self._busy:
            self.status.config(text="準備OKです。ボタンを押してください。")

    # ---------- 書き出し
    def start(self):
        if self._busy:
            return
        out = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), title="動画の保存先と名前を決めてください",
            defaultextension=".mp4", filetypes=[("MP4動画", "*.mp4")],
            initialfile=config.DEFAULT_FILENAME)
        if not out:
            return
        self.state.save_prefs()
        params = self.state.export_params(out)
        self._out = out
        self._cancel = threading.Event()
        self._set_busy(True)
        self.after_box.grid_remove()
        self.bar["value"] = 0
        self.status.config(text="動画を作っています。しばらくお待ちください…")

        run_async(self,
                  lambda progress: export_video(params, progress, self._cancel),
                  self._on_done, self._on_error, on_progress=self._on_progress)

    def cancel(self):
        if self._cancel:
            self._cancel.set()
            self.status.config(text="中止しています…")

    def _on_progress(self, pct, msg):
        self.bar["value"] = pct
        self.status.config(text=msg)

    def _on_done(self, _result):
        self._set_busy(False)
        self.bar["value"] = 100
        self.status.config(text=f"完成しました!\n保存先: {self._out}")
        self.after_box.grid(row=4, column=0, sticky="ew", pady=(10, 0))

    def _on_error(self, err):
        self._set_busy(False)
        if isinstance(err, ExportCancelled):
            self.bar["value"] = 0
            self.status.config(text="中止しました。")
        else:
            self.status.config(text="うまく作れませんでした。")
            self.error(str(err))

    def _set_busy(self, busy):
        self._busy = busy
        self.make_btn.config(state="disabled" if busy else "normal")
        if busy:
            self._btns.add(self.cancel_btn)
        else:
            self.cancel_btn.grid_forget()
            if self.cancel_btn in self._btns._items:
                self._btns._items.remove(self.cancel_btn)
        self.ctx.wizard.set_nav_enabled(not busy)

    def restart(self):
        if self.confirm("写真と文章を消して、最初からやり直しますか?"):
            self.state.reset()
            for step in self.ctx.wizard.steps:      # 作成済みの画面の中身も初期化
                if step is not None and hasattr(step, "reset"):
                    step.reset()
            self.ctx.wizard.show(0)
