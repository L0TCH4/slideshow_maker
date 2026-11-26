"""ステップ1: 写真を選ぶ"""
import os
import tkinter as tk
from tkinter import filedialog, ttk

from ... import config
from ...core.files import collect_images
from ...core.render import render_photo_preview
from ...state import Photo
from .. import dnd
from ..widgets import FlowFrame, PreviewPane, ResponsiveColumns, WrapLabel
from .base import Step


class PhotosStep(Step):
    title = "写真を選ぶ"
    description = "動画に使う写真を追加します。上にある写真から順番に動画になります。"

    def build(self, body):
        body.rowconfigure(1, weight=1)

        bar = FlowFrame(body)
        bar.grid(row=0, column=0, sticky="ew")
        bar.add(ttk.Button(bar, text="写真を追加する", style="Primary.TButton",
                           command=self.add_dialog))
        bar.add(ttk.Button(bar, text="↑ 前へ", command=lambda: self.move(-1)))
        bar.add(ttk.Button(bar, text="↓ 後ろへ", command=lambda: self.move(1)))
        bar.add(ttk.Button(bar, text="削除", command=self.remove))
        bar.add(ttk.Button(bar, text="全部消す", command=self.clear))
        bar.add(ttk.Button(bar, text="すべてリセットする", style="Danger.TButton",
                           command=self.reset_all))

        cols = ResponsiveColumns(body)
        cols.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        L = cols.left
        L.rowconfigure(0, weight=1)
        L.columnconfigure(0, weight=1)
        self.listbox = tk.Listbox(L, exportselection=False, activestyle="none", height=8)
        sb = ttk.Scrollbar(L, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.listbox.bind("<<ListboxSelect>>", lambda e: self.preview.refresh())

        R = cols.right
        R.rowconfigure(0, weight=1)
        R.columnconfigure(0, weight=1)
        self.preview = PreviewPane(
            R, self._render, min_size=(240, 170),
            placeholder="ここに写真が表示されます\n\n写真をドラッグ&ドロップするか、\n「写真を追加する」を押してください"
            if dnd.HAS_DND else
            "ここに写真が表示されます\n\n「写真を追加する」を押してください")
        self.preview.grid(row=0, column=0, sticky="nsew")

        tip = ("※ 写真(フォルダも可)をこの画面にドラッグ&ドロップしても追加できます。"
               if dnd.HAS_DND else
               "※ ドラッグ&ドロップを使うには「pip install tkinterdnd2」を実行してください。")
        self.count_lbl = WrapLabel(body, style="Hint.TLabel", text=tip)
        self.count_lbl.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self._tip = tip

        # 前回の続きを読み込んだときの案内(最初に開いたときだけ出す)
        self.note_lbl = WrapLabel(body, foreground=config.COLORS["accent"])
        self.note_lbl.grid(row=3, column=0, sticky="ew", pady=(6, 0))

        dnd.enable_file_drop(self, self.add_paths)

    # ---------- 表示
    def on_show(self):
        self._refresh_list(keep=self._selected())
        note = self.state.restore_note
        self.note_lbl.config(text=note)
        if note:
            self.note_lbl.grid()
        else:
            self.note_lbl.grid_remove()
        self.state.restore_note = ""          # 案内は1回だけ

    def _selected(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def _refresh_list(self, select=None, keep=None):
        idx = select if select is not None else keep
        self.listbox.delete(0, "end")
        for i, p in enumerate(self.state.photos):
            self.listbox.insert("end", f"{i + 1}枚目   {os.path.basename(p.path)}")
        if self.state.photos:
            idx = 0 if idx is None else max(0, min(idx, len(self.state.photos) - 1))
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
        n = len(self.state.photos)
        self.count_lbl.config(text=(f"現在 {n} 枚の写真があります。\n" if n else "") + self._tip)
        self.preview.refresh()

    def _render(self, w, h):
        i = self._selected()
        if i is None:
            return None
        return render_photo_preview(self.state.photos[i].path, (w, h))

    # ---------- 操作
    def add_dialog(self):
        paths = filedialog.askopenfilenames(parent=self.winfo_toplevel(),
                                            title="写真を選んでください(複数選べます)",
                                            filetypes=config.IMG_FILETYPES)
        if paths:
            self.add_paths(list(paths))

    def add_paths(self, paths):
        files = collect_images(paths)
        if not files:
            self.info("追加できる写真が見つかりませんでした。\n"
                      "(png / jpg / bmp / gif / webp / tif に対応しています)")
            return
        first_new = len(self.state.photos)
        self.state.photos.extend(Photo(f) for f in files)
        self._refresh_list(select=first_new)

    def remove(self):
        i = self._selected()
        if i is None:
            self.info("消したい写真をクリックして選んでください。")
            return
        del self.state.photos[i]
        self._refresh_list(select=i)

    def reset_all(self):
        """写真・文章・テロップ・動画の設定を、すべて最初の状態に戻す(確認つき)。"""
        if not self.confirm(
                "すべてリセットします。\n\n"
                "・写真の一覧\n・書いた文章とテロップ\n・動画の設定(長さ・フォント・色など)\n\n"
                "がすべて最初の状態に戻ります。この操作は取り消せません。\n"
                "(APIキーは消えません)\n\nよろしいですか?",
                title="すべてリセットする"):
            return
        self.state.reset_all()
        for step in self.ctx.wizard.steps:          # 作成済みの画面の中身も初期化
            if step is not None and hasattr(step, "reset"):
                step.reset()
        self.note_lbl.config(text="")
        self.note_lbl.grid_remove()
        self._refresh_list()

    def clear(self):
        if self.state.photos and self.confirm("すべての写真をリストから消しますか?"):
            self.state.photos.clear()
            self._refresh_list()

    def move(self, d):
        i = self._selected()
        if i is None:
            self.info("動かしたい写真をクリックして選んでください。")
            return
        j = i + d
        ph = self.state.photos
        if 0 <= j < len(ph):
            ph[i], ph[j] = ph[j], ph[i]
            self._refresh_list(select=j)

    def can_go_next(self):
        if not self.state.photos:
            self.info("先に「写真を追加する」で、写真を1枚以上選んでください。")
            return False
        return True
