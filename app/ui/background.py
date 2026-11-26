"""時間のかかる処理(AI通信・動画の書き出し)を、画面を固めずに裏で実行する。"""
import queue
import threading


def run_async(widget, func, on_success, on_error, on_progress=None):
    """func(progress) を別スレッドで実行し、結果は画面のスレッドで受け取る。

    func    : progress(*args) を呼べる関数。例外が出れば on_error(例外) が呼ばれる
    on_*    : すべて画面を操作してよい(メインスレッドで呼ばれる)
    """
    q = queue.Queue()

    def progress(*args):
        q.put(("progress", args))

    def target():
        try:
            q.put(("ok", func(progress)))
        except BaseException as e:      # noqa: キャンセルなども含めて受け取る
            q.put(("err", e))

    threading.Thread(target=target, daemon=True).start()

    def poll():
        try:
            while True:
                kind, val = q.get_nowait()
                if kind == "progress":
                    if on_progress:
                        on_progress(*val)
                elif kind == "ok":
                    on_success(val)
                    return
                else:
                    on_error(val)
                    return
        except queue.Empty:
            pass
        try:
            if widget.winfo_exists():
                widget.after(100, poll)
        except Exception:
            pass

    widget.after(100, poll)
