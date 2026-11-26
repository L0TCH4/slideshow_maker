"""使えるフォントの一覧。GUI には依存しません。"""
import os

from .. import config


def font_label(path):
    """フォントのパスから、画面に出す名前を作る。"""
    if not path:
        return "自動(標準)"
    base = os.path.basename(path)
    return config.FONT_LABELS.get(base, os.path.splitext(base)[0])

def available_fonts():
    """システムにあるフォントすべての [(表示名, パス), ...]。
    config.FONT_CANDIDATES のものを先頭に(日本語向けの優先候補)、残りを名前順で続けます。"""
    out, seen = [], set()

    # 1) これまで通りの優先候補を先頭に
    for p in config.FONT_CANDIDATES:
        if os.path.exists(p) and p not in seen:
            seen.add(p)
            out.append((font_label(p), p))

    # 2) フォントフォルダを走査して、残りを全部追加
    rest = []
    for d in config.FONT_DIRS:
        if not d or not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for f in files:
                if f.lower().endswith(config.FONT_EXTENSIONS):
                    p = os.path.join(root, f)
                    if p not in seen:
                        seen.add(p)
                        rest.append((font_label(p), p))
    rest.sort(key=lambda x: x[0].lower())
    return out + rest
