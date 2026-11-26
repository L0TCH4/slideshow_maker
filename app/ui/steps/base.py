"""すべてのステップ(画面)のひな形。新しいステップを作るときは、これを継承します。"""
from tkinter import messagebox, ttk

from ..widgets import ScrollFrame


class Step(ttk.Frame):
    # ---- 子クラスで書き換える項目
    title = "ステップ名"                 # 画面上部の大見出し
    description = "このステップの説明"   # 見出しの下に出る説明文
    next_label = "次へ →"               # 「次へ」ボタンの文字
    show_next = True                    # False にすると「次へ」ボタンを隠す(最後の画面用)

    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.state = ctx.state
        self.fonts = ctx.fonts
        # 画面が小さいときも内容が埋もれないよう、全ステップをスクロール可能な枠に入れる
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)
        self.body = self.scroll.inner
        self.body.columnconfigure(0, weight=1)
        self.build(self.body)

    # ---- 子クラスで実装する部分
    def build(self, body):
        """部品を body に並べる(最初に1回だけ呼ばれる)。"""
        raise NotImplementedError

    def on_show(self):
        """このステップが表示されるたびに呼ばれる。最新の状態を画面に反映する。"""

    def on_hide(self):
        """別のステップに移るときに呼ばれる。入力内容を state に保存する。"""

    def flush(self):
        """自動保存の直前に呼ばれる。入力途中の内容(文章欄など)を state に取り込む。"""

    def can_go_next(self):
        """「次へ」を押したとき、進んでよいか。だめなら説明を出して False を返す。"""
        return True

    # ---- 便利メソッド
    def info(self, message, title="お知らせ"):
        messagebox.showinfo(title, message, parent=self.winfo_toplevel())

    def error(self, message, title="エラー"):
        messagebox.showerror(title, message, parent=self.winfo_toplevel())

    def confirm(self, message, title="確認"):
        return messagebox.askyesno(title, message, parent=self.winfo_toplevel())
