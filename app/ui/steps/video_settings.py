"""ステップ5: 動画の設定(長さ・ズーム・フォント・文字色・BGM)
全体の設定に加えて、写真ごとに「長さ・フォント・文字色」を変えられます。"""
import os
import tkinter as tk
from tkinter import filedialog, ttk

from ... import config
from ...core.render import render_preview
from ...core.video import check_timing
from ..fields import ColorField, FontField
from ..widgets import FlowFrame, PreviewPane, ResponsiveColumns, WrapLabel
from .base import Step

SAMPLE_TEXT = "文字の見本\nテロップのサンプル"   # テロップが空の写真のプレビューに使う文字


class VideoSettingsStep(Step):
    title = "動画の設定"
    description = ("1枚の長さ・フォント・文字の色などを決めます。"
                   "特定の写真だけ変えたいときは、下の「写真ごとの設定」を使います。")

    def build(self, body):
        s = self.state
        self._adv_open = False
        self._loading = False          # 画面の値を読み込み中は、写真への書き戻しをしない

        # ================= 全体の設定 =================
        box = ttk.LabelFrame(body, text=" 全体の設定(すべての写真に使われます) ", padding=10)
        box.grid(row=0, column=0, sticky="ew")
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="1枚の長さ").grid(row=0, column=0, sticky="w", pady=4)
        f = ttk.Frame(box)
        f.grid(row=0, column=1, sticky="w", padx=(10, 0))
        lo, hi = config.DURATION_RANGE
        ttk.Spinbox(f, from_=lo, to=hi, increment=0.5, width=6,
                    textvariable=s.duration).pack(side="left")
        ttk.Label(f, text="秒").pack(side="left", padx=6)

        ttk.Checkbutton(box, text="ゆっくりズーム効果を入れる (Ken Burns)",
                        variable=s.kenburns).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(box, text="フォント").grid(row=2, column=0, sticky="w", pady=4)
        FontField(box, s.font_path).grid(row=2, column=1, sticky="ew", padx=(10, 0))

        ttk.Label(box, text="文字の色").grid(row=3, column=0, sticky="nw", pady=(8, 0))
        ColorField(box, s.text_color).grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))

        ttk.Label(box, text="BGM(音楽)").grid(row=4, column=0, sticky="nw", pady=(8, 0))
        bgm = FlowFrame(box)
        bgm.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))
        self.audio_lbl = bgm.add(ttk.Label(bgm, text="なし"))
        bgm.add(ttk.Button(bgm, text="選ぶ", command=self.choose_audio))
        bgm.add(ttk.Button(bgm, text="なし", command=self.clear_audio))

        self.total_lbl = WrapLabel(body, style="Hint.TLabel")
        self.total_lbl.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        # ================= 写真ごとの設定 =================
        per = ttk.LabelFrame(body, text=" 写真ごとの設定(特定の写真だけ変えたいとき) ", padding=10)
        per.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        per.columnconfigure(0, weight=1)
        WrapLabel(per, style="Hint.TLabel",
                  text="左の一覧から写真を選び、変えたい項目にチェックを入れてください。"
                       "チェックしない項目は、上の「全体の設定」が使われます。★は個別設定ありの写真です。"
                  ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        cols = ResponsiveColumns(per, left_weight=2, right_weight=3)
        cols.grid(row=1, column=0, sticky="ew")

        L = cols.left
        L.columnconfigure(0, weight=1)
        self.listbox = tk.Listbox(L, exportselection=False, activestyle="none", height=7)
        sb = ttk.Scrollbar(L, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())
        btns = FlowFrame(L)
        btns.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        btns.add(ttk.Button(btns, text="この写真を全体の設定に戻す", command=self._clear_one))
        btns.add(ttk.Button(btns, text="全部の写真を戻す", command=self._clear_all))

        R = cols.right
        R.columnconfigure(0, weight=1)
        self.preview = PreviewPane(R, self._render, min_size=(240, 210),
                                   placeholder="写真を選ぶと、フォントや色を変えた\n仕上がりイメージが出ます")
        self.preview.grid(row=0, column=0, sticky="ew")

        ov = ttk.LabelFrame(R, text=" 選んだ写真だけ変える ", padding=8)
        ov.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ov.columnconfigure(0, weight=1)
        mv = dict(master=self.winfo_toplevel())
        self.dur_on = tk.BooleanVar(value=False, **mv)
        self.sel_dur = tk.DoubleVar(value=config.DEFAULTS["duration"], **mv)
        self.font_on = tk.BooleanVar(value=False, **mv)
        self.sel_font = tk.StringVar(value="", **mv)
        self.color_on = tk.BooleanVar(value=False, **mv)
        self.sel_color = tk.StringVar(value=config.DEFAULTS["text_color"], **mv)

        ttk.Checkbutton(ov, text="この写真の長さを変える", variable=self.dur_on).grid(
            row=0, column=0, sticky="w")
        df = ttk.Frame(ov)
        df.grid(row=1, column=0, sticky="w", padx=(28, 0))
        self.dur_spin = ttk.Spinbox(df, from_=lo, to=hi, increment=0.5, width=6,
                                    textvariable=self.sel_dur)
        self.dur_spin.pack(side="left")
        ttk.Label(df, text="秒").pack(side="left", padx=6)

        ttk.Checkbutton(ov, text="この写真のフォントを変える", variable=self.font_on).grid(
            row=2, column=0, sticky="w", pady=(8, 0))
        self.font_field = FontField(ov, self.sel_font)
        self.font_field.grid(row=3, column=0, sticky="ew", padx=(28, 0))

        ttk.Checkbutton(ov, text="この写真の文字の色を変える", variable=self.color_on).grid(
            row=4, column=0, sticky="w", pady=(8, 0))
        self.color_field = ColorField(ov, self.sel_color)
        self.color_field.grid(row=5, column=0, sticky="ew", padx=(28, 0))

        # 個別設定の変更 → 写真に書き戻す
        for v in (self.dur_on, self.sel_dur, self.font_on, self.sel_font,
                  self.color_on, self.sel_color):
            v.trace_add("write", lambda *a: self._apply_override())
        # 全体設定の変更 → 表示を更新(個別設定がない項目は全体の値に追従する)
        for v in (s.duration, s.font_path, s.text_color, s.fade, s.shape,
                  s.telop_size, s.telop_pos):
            v.trace_add("write", lambda *a: self._on_global_change())

        # ================= くわしい設定 =================
        self.adv_btn = ttk.Button(body, text="▶ くわしい設定を開く", command=self._toggle_adv)
        self.adv_btn.grid(row=3, column=0, sticky="w", pady=(12, 0))
        self.adv = ttk.LabelFrame(body, text=" くわしい設定 ", padding=10)
        self.adv.columnconfigure(1, weight=1)
        ttk.Label(self.adv, text="切り替えの長さ").grid(row=0, column=0, sticky="w", pady=4)
        f2 = ttk.Frame(self.adv)
        f2.grid(row=0, column=1, sticky="w", padx=(10, 0))
        flo, fhi = config.FADE_RANGE
        ttk.Spinbox(f2, from_=flo, to=fhi, increment=0.1, width=6,
                    textvariable=s.fade).pack(side="left")
        ttk.Label(f2, text="秒 (0で瞬時に切り替え)").pack(side="left", padx=6)
        ttk.Label(self.adv, text="コマ数(FPS)").grid(row=1, column=0, sticky="w", pady=4)
        plo, phi = config.FPS_RANGE
        ttk.Spinbox(self.adv, from_=plo, to=phi, increment=5, width=6,
                    textvariable=s.fps).grid(row=1, column=1, sticky="w", padx=(10, 0))
        WrapLabel(self.adv, style="Hint.TLabel",
                  text="テロップが「□」になるときは、日本語に対応したフォントを上のフォント欄で選んでください。"
                  ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    # ================= 表示 =================
    def on_show(self):
        sel = self._selected()
        self._fill_list(sel if sel is not None else 0)
        self._load_selected()
        self._update_total()
        self.audio_lbl.config(text=os.path.basename(self.state.audio_path.get()) or "なし")

    def reset(self):
        """「すべてリセット」「最初からやり直す」のとき、一覧と個別設定欄を初期化する。"""
        self._fill_list(0)
        self._load_selected()
        self._update_total()
        self.preview.refresh()

    def _selected(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def _photo(self):
        i = self._selected()
        return self.state.photos[i] if i is not None else None

    def _row_text(self, i):
        s, p = self.state, self.state.photos[i]
        mark = "  ★" if p.has_override() else ""
        return f"{i + 1}枚目  {os.path.basename(p.path)}  {s.duration_for(p):g}秒{mark}"

    def _fill_list(self, select):
        self.listbox.delete(0, "end")
        for i in range(len(self.state.photos)):
            self.listbox.insert("end", self._row_text(i))
        if self.state.photos:
            select = max(0, min(select, len(self.state.photos) - 1))
            self.listbox.selection_set(select)
            self.listbox.see(select)

    def _refresh_row(self):
        i = self._selected()
        if i is None:
            return
        self.listbox.delete(i)
        self.listbox.insert(i, self._row_text(i))
        self.listbox.selection_set(i)

    def _update_total(self):
        s = self.state
        sec = s.total_seconds()
        self.total_lbl.config(
            text=f"写真 {len(s.photos)} 枚 → 動画の長さは約 {sec:.0f} 秒({sec / 60:.1f} 分)になります。")

    def _render(self, w, h):
        p = self._photo()
        if p is None:
            return None
        s = self.state
        caption = p.caption if p.caption.strip() else SAMPLE_TEXT
        return render_preview(p.path, caption, s.shape_size(), (w, h), s.font_for(p),
                              float(s.telop_size.get()), float(s.telop_pos.get()),
                              text_color=s.color_for(p))

    # ================= 写真ごとの設定 =================
    def _on_select(self):
        self._load_selected()
        self.preview.refresh()

    def _load_selected(self):
        """選んだ写真の設定を、画面の入力欄に読み込む。"""
        p = self._photo()
        s = self.state
        self._loading = True
        try:
            self.dur_on.set(bool(p) and p.duration is not None)
            self.sel_dur.set(p.duration if (p and p.duration is not None) else s.duration_for_default())
            self.font_on.set(bool(p) and bool(p.font_path))
            self.sel_font.set(p.font_path if (p and p.font_path) else s.font_path.get())
            self.color_on.set(bool(p) and bool(p.text_color))
            self.sel_color.set(p.text_color if (p and p.text_color) else s.text_color.get())
        finally:
            self._loading = False
        self._set_enabled()

    def _set_enabled(self):
        has = self._photo() is not None
        self.dur_spin.config(state="normal" if (has and self.dur_on.get()) else "disabled")
        self.font_field.set_enabled(has and self.font_on.get())
        self.color_field.set_enabled(has and self.color_on.get())

    def _apply_override(self):
        """入力欄の内容を、選んでいる写真に書き戻す。"""
        if self._loading:
            return
        p = self._photo()
        if p is None:
            return
        if self.dur_on.get():
            try:
                p.duration = float(self.sel_dur.get())
            except (tk.TclError, ValueError):
                pass                                   # 入力途中は無視
        else:
            p.duration = None
        p.font_path = self.sel_font.get().strip() if self.font_on.get() else ""
        p.text_color = self.sel_color.get().strip() if self.color_on.get() else ""
        self._set_enabled()
        if not (self.dur_on.get() and self.font_on.get() and self.color_on.get()):
            self._show_global_for_unchecked()
        self._refresh_row()
        self._update_total()
        self.preview.refresh()

    def _show_global_for_unchecked(self):
        """チェックを外した項目は、入力欄に「全体の設定」の値を見せておく。"""
        s = self.state
        self._loading = True
        try:
            if not self.dur_on.get():
                self.sel_dur.set(s.duration_for_default())
            if not self.font_on.get():
                self.sel_font.set(s.font_path.get())
            if not self.color_on.get():
                self.sel_color.set(s.text_color.get())
        finally:
            self._loading = False

    def _on_global_change(self):
        if self._loading:
            return
        self._show_global_for_unchecked()
        sel = self._selected()
        if sel is not None:
            self._fill_list(sel)
        self._update_total()
        self.preview.refresh()

    def _clear_one(self):
        p = self._photo()
        if p is None:
            self.info("写真を一覧から選んでください。")
            return
        p.clear_override()
        self._after_clear()

    def _clear_all(self):
        if not any(p.has_override() for p in self.state.photos):
            self.info("個別設定をした写真はありません。")
            return
        if self.confirm("すべての写真の個別設定をやめて、全体の設定に戻しますか?"):
            for p in self.state.photos:
                p.clear_override()
            self._after_clear()

    def _after_clear(self):
        sel = self._selected()
        self._fill_list(sel if sel is not None else 0)
        self._load_selected()
        self._update_total()
        self.preview.refresh()

    # ================= その他 =================
    def _toggle_adv(self):
        self._adv_open = not self._adv_open
        if self._adv_open:
            self.adv.grid(row=4, column=0, sticky="ew", pady=(6, 0))
            self.adv_btn.config(text="▼ くわしい設定を閉じる")
        else:
            self.adv.grid_forget()
            self.adv_btn.config(text="▶ くわしい設定を開く")

    def choose_audio(self):
        p = filedialog.askopenfilename(parent=self.winfo_toplevel(),
                                       title="BGMにする音楽を選んでください",
                                       filetypes=config.AUDIO_FILETYPES)
        if p:
            self.state.audio_path.set(p)
            self.audio_lbl.config(text=os.path.basename(p))

    def clear_audio(self):
        self.state.audio_path.set("")
        self.audio_lbl.config(text="なし")

    def can_go_next(self):
        s = self.state
        try:
            durations = [s.duration_for(p) for p in s.photos]
            fade, fps = float(s.fade.get()), int(s.fps.get())
        except (tk.TclError, ValueError):
            self.error("秒数やコマ数は、数字で入力してください。")
            return False
        msg = check_timing(durations, fade, fps)
        if msg:
            self.error(msg + "\n(「くわしい設定」で切り替えの長さを変えられます)")
            return False
        return True
