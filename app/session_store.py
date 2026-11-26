"""編集中の内容(写真・文章・テロップ・設定)を、ファイルに自動保存・復元する。
APIキーなどの「設定」は settings_store.py、こちらは「作業内容」です。"""
import json
import os
import sys

from . import config

VERSION = 1


def load():
    """前回の作業内容を返す。なければ(壊れていても)None。"""
    try:
        with open(config.SESSION_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("version") == VERSION:
            return data
    except Exception:
        pass
    return None


def save(data):
    """書き込み途中で止まっても壊れないよう、一時ファイルに書いてから置き換える。"""
    tmp = config.SESSION_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, config.SESSION_PATH)
    except Exception as e:
        print(f"自動保存できませんでした: {e}", file=sys.stderr)


def clear():
    try:
        os.remove(config.SESSION_PATH)
    except OSError:
        pass
