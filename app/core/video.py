"""スライドショー動画(MP4)の書き出し。GUI には依存しません。"""
import bisect
import collections
import os
import subprocess
import threading
from dataclasses import dataclass, field

from PIL import Image

from .. import config
from .render import Slide, SlideSpec


class ExportCancelled(Exception):
    """利用者が中止した。"""


@dataclass
class ExportParams:
    photos: list                    # [SlideSpec, ...] 写真ごとの秒数・フォント・色も入っている
    out_path: str
    size: tuple                     # (幅, 高さ)
    fade: float = 0.5               # 切り替えの秒数
    fps: int = 30
    kenburns: bool = True
    font_pct: float = 6.0
    pos_pct: float = 90.0
    audio_path: str = ""


def timeline(durations, fade):
    """各写真が出始める時刻の一覧と、動画全体の長さ(秒)を返す。
    次の写真は、前の写真の終わりより fade 秒だけ早く出始める(フェードで重なる)。"""
    starts, t = [], 0.0
    for d in durations:
        starts.append(t)
        t += d - fade
    total = starts[-1] + durations[-1] if durations else 0.0
    return starts, total


def total_seconds(durations, fade):
    return timeline(list(durations), fade)[1]


def check_timing(durations, fade, fps):
    """秒数などに問題があれば、日本語のメッセージを返す。問題なければ None。
    durations は、数字1つでも、写真ごとの数字のリストでもよい。"""
    ds = [durations] if isinstance(durations, (int, float)) else list(durations)
    if not ds:
        return None
    if min(ds) <= 0 or fps <= 0 or fade < 0:
        return "秒数やコマ数は 0 より大きい数字にしてください。"
    if fade > min(ds) / 2:
        return ("切り替えの長さは、いちばん短い写真の長さの半分以下にしてください。"
                f"(いまの切り替え: {fade:g} 秒 / いちばん短い写真: {min(ds):g} 秒)")
    return None


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def export_video(p: ExportParams, progress=None, cancel: threading.Event = None):
    """動画を書き出す。progress(0〜100, メッセージ) で進み具合を知らせる。"""
    progress = progress or (lambda pct, msg: None)
    durations = [sp.duration for sp in p.photos]
    err = check_timing(durations, p.fade, p.fps)
    if err:
        raise ValueError(err)
    if not p.photos:
        raise ValueError("写真がありません。")

    W, H = p.size
    n = len(p.photos)
    starts, total = timeline(durations, p.fade)
    total_frames = max(1, round(total * p.fps))
    enc = config.VIDEO_ENCODE

    cmd = [ffmpeg_exe(), "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(p.fps), "-i", "-"]
    if p.audio_path:
        cmd += ["-stream_loop", "-1", "-i", p.audio_path]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(enc["crf"]),
            "-preset", enc["preset"]]
    if p.audio_path:
        cmd += ["-c:a", "aac", "-b:a", enc["audio_bitrate"], "-map", "0:v:0", "-map", "1:a:0",
                "-shortest"]
    cmd += ["-movflags", "+faststart", p.out_path]

    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, creationflags=flags)
    except FileNotFoundError:
        raise RuntimeError("動画変換ソフト(ffmpeg)が見つかりません。\n"
                           "「pip install imageio-ffmpeg」を実行してください。")

    tail = collections.deque(maxlen=12)         # ffmpeg のエラー表示を覚えておく

    def drain():
        for line in proc.stderr:
            tail.append(line.decode("utf-8", "replace").rstrip())
    threading.Thread(target=drain, daemon=True).start()

    slides = {}

    def get(i):
        if i not in slides:
            slides[i] = Slide(p.photos[i], i, (W, H), p.kenburns, p.font_pct, p.pos_pct)
        return slides[i]

    try:
        for f in range(total_frames):
            if cancel is not None and cancel.is_set():
                raise ExportCancelled()
            t = f / p.fps
            i = max(0, bisect.bisect_right(starts, t) - 1)   # 今出ている写真
            local = t - starts[i]
            cur = get(i).frame(local / durations[i])
            if i > 0 and p.fade > 0 and local < p.fade:      # 前の写真とフェードで重ねる
                prev = get(i - 1).frame((t - starts[i - 1]) / durations[i - 1])
                frame = Image.blend(prev, cur, local / p.fade)
            else:
                frame = cur
            proc.stdin.write(frame.tobytes())

            for k in [k for k in slides if k < i - 1]:   # 使い終わった分はメモリから外す
                del slides[k]
            if f % 10 == 0:
                pct = f / total_frames * 100
                progress(pct, f"動画を作っています… {int(pct)}%")

        proc.stdin.close()
        code = proc.wait()
        if code != 0:
            raise RuntimeError("動画への変換に失敗しました。\n\n" + "\n".join(tail))
        progress(100, "完成しました!")
    except ExportCancelled:
        _stop(proc, p.out_path)
        raise
    except BrokenPipeError:
        _stop(proc, None)
        raise RuntimeError("動画変換ソフト(ffmpeg)が途中で止まりました。\n\n" + "\n".join(tail))
    except Exception:
        _stop(proc, p.out_path)
        raise


def _stop(proc, remove_path):
    try:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
    except Exception:
        pass
    if remove_path and os.path.exists(remove_path):
        try:
            os.remove(remove_path)
        except OSError:
            pass
