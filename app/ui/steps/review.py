"""ステップ4: AIが作ったテロップを確認・手直しする(見た目の調整もここ)"""
import os
import tkinter as tk
from tkinter import ttk

from ... import config
from ...core.render import render_preview
from ..widgets import PreviewPane, ResponsiveColumns, WrapLabel
from .base import Step


class ReviewStep(Step):
    title = "テロップを確認する"
    description = ("AIが作ったテロップを確認します。直したいときは、写真を選んで文字を書き換えてください。"
                   "文字の位置や大きさも、ここで調整できます。")

    def build(self, body):
        self._updating = False
        body.rowconfigure(0, weight=1)

        cols = ResponsiveColumns(body, left_weight=2, right_weight=3)
        cols.grid(row=0, column=0, sticky="nsew")

        # ---- 左: 写真ごとのテロップ一覧
        L = cols.left
        L.rowconfigure(1, weight=1)
        L.columnconfigure(0, weight=1)
        ttk.Label(L, text="写真ごとのテロップ", font=self.fonts.step).grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.listbox = tk.Listbox(L, exportselection=False, activestyle="none", height=8)
        sb = ttk.Scrollbar(L, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        self.listbox.grid(row=1, column=0, sticky="nsew")
        sb.grid(row=1, column=1, sticky="ns")
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # ---- 右: プレビュー / 編集 / 見た目
        R = cols.right
        R.columnconfigure(0, weight=1)
        R.rowconfigure(0, weight=1)
        self.preview = PreviewPane(R, self._render, min_size=(260, 170),
                                   placeholder="写真を選ぶと、仕上がりイメージが出ます")
        self.preview.grid(row=0, column=0, sticky="nsew")

        edit = ttk.LabelFrame(R, text=" この写真のテロップ(書き換えできます) ", padding=6)
        edit.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        edit.columnconfigure(0, weight=1)
        self.text = tk.Text(edit, height=3, wrap="word", font="TkDefaultFont", undo=True)
        self.text.grid(row=0, column=0, sticky="ew")
        self.text.bind("<<Modified>>", self._on_text_modified)

        look = ttk.LabelFrame(R, text=" 見た目 ", padding=6)
        look.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        look.columnconfigure(2, weight=1)
        s = self.state

        ttk.Label(look, text="動画の形").grid(row=0, column=0, sticky="w")
        ttk.Combobox(look, textvariable=s.shape, values=list(config.SHAPES),
                     state="readonly").grid(row=0, column=1, columnspan=3, sticky="ew", padx=(8, 0))

        lo, hi = config.TELOP_SIZE_RANGE
        for r, (label, var, a, b, lo_, hi_) in enumerate(
                [("文字の高さ", s.telop_pos, "上", "下", 0, 100),
                 ("文字の大きさ", s.telop_size, "小", "大", lo, hi)], start=1):
            ttk.Label(look, text=label).grid(row=r, column=0, sticky="w", pady=(6, 0))
            ttk.Label(look, text=a).grid(row=r, column=1, padx=6, pady=(6, 0))
            ttk.Scale(look, from_=lo_, to=hi_, variable=var).grid(
                row=r, column=2, sticky="ew", pady=(6, 0))
            ttk.Label(look, text=b).grid(row=r, column=3, padx=6, pady=(6, 0))

        for v in (s.shape, s.telop_pos, s.telop_size, s.font_path, s.text_color):
            v.trace_add("write", lambda *a: self.preview.refresh())

    # ---------- 表示
    def on_show(self):
        sel = self._selected()
        self._fill_list(sel if sel is not None else 0)

    def reset(self):
        """「すべてリセット」「最初からやり直す」のとき、一覧と入力欄を空にする。"""
        self.listbox.delete(0, "end")
        self._load_caption()
        self.preview.refresh()

    def _selected(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def _row_text(self, i):
        p = self.state.photos[i]
        first = p.caption.strip().split("\n")[0] if p.caption.strip() else "(文字なし)"
        return f"{i + 1}枚目  {first}"

    def _fill_list(self, select):
        self.listbox.delete(0, "end")
        for i in range(len(self.state.photos)):
            self.listbox.insert("end", self._row_text(i))
        if self.state.photos:
            select = max(0, min(select, len(self.state.photos) - 1))
            self.listbox.selection_set(select)
            self.listbox.see(select)
        self._load_caption()
        self.preview.refresh()

    def _on_select(self, _e=None):
        self._load_caption()
        self.preview.refresh()

    # ---------- 編集
    def _load_caption(self):
        i = self._selected()
        self._updating = True
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        if i is not None:
            self.text.insert("1.0", self.state.photos[i].caption)
        else:
            self.text.config(state="disabled")
        self.text.edit_modified(False)
        self._updating = False

    def _on_text_modified(self, _e=None):
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        if self._updating:
            return
        i = self._selected()
        if i is None:
            return
        self.state.photos[i].caption = self.text.get("1.0", "end-1c")
        self.listbox.delete(i)
        self.listbox.insert(i, self._row_text(i))
        self.listbox.selection_set(i)
        self.preview.refresh()

    def _render(self, w, h):
        i = self._selected()
        if i is None:
            return None
        s = self.state
        ph = s.photos[i]
        return render_preview(ph.path, ph.caption, s.shape_size(), (w, h),
                              s.font_for(ph), float(s.telop_size.get()),
                              float(s.telop_pos.get()), text_color=s.color_for(ph))
