"""ドラッグ&ドロップ対応(tkinterdnd2 が入っているときだけ有効。なくても動きます)。"""
import tkinter as tk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:
    HAS_DND = False


def create_root():
    return TkinterDnD.Tk() if HAS_DND else tk.Tk()


def enable_file_drop(widget, callback):
    """widget とその中のすべての部品に、ファイルのドロップを受け付けさせる。
    callback(パスのリスト) が呼ばれる。"""
    if not HAS_DND:
        return

    def on_drop(event):
        callback(list(widget.tk.splitlist(event.data)))   # 空白入りのパスにも対応
        return event.action

    def register(w):
        try:
            w.drop_target_register(DND_FILES)
            w.dnd_bind("<<Drop>>", on_drop)
        except Exception:
            pass
        for child in w.winfo_children():
            register(child)

    register(widget)
