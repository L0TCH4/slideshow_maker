"""APIキーなど、次回も使いたい設定をファイルに保存・読み込みする。"""
import json
import os
import sys

from . import config


def load():
    try:
        with open(config.USER_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save(data):
    try:
        with open(config.USER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(config.USER_CONFIG_PATH, 0o600)  # 自分だけが読めるようにする
        except Exception:
            pass
    except Exception as e:
        print(f"設定を保存できませんでした: {e}", file=sys.stderr)
