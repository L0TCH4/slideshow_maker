"""ファイル・フォルダのパスから、使える画像だけを集める。"""
import os

from .. import config


def collect_images(paths):
    """ファイルやフォルダのパス一覧から、画像ファイルのパスだけを順に返す。
    フォルダが渡されたら、その中の画像を名前順に追加する。"""
    out = []
    for p in paths:
        if os.path.isdir(p):
            for name in sorted(os.listdir(p)):
                fp = os.path.join(p, name)
                if os.path.isfile(fp) and _is_image(fp):
                    out.append(fp)
        elif os.path.isfile(p) and _is_image(p):
            out.append(p)
    return out


def _is_image(path):
    return os.path.splitext(path)[1].lower() in config.IMG_EXTS
