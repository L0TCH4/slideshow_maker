"""Gemini API との通信。GUI には依存しません。(標準ライブラリだけで動きます)"""
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

from .. import config
from ..prompts import build_telop_prompt


def call_gemini(api_key, model, prompt, json_mode=False, timeout=None):
    """Gemini API (generateContent) に文章を送り、返ってきたテキストを返す。"""
    cfg = config.GEMINI
    timeout = timeout or cfg["timeout"]
    gen = {"temperature": cfg["temperature"]}
    if json_mode:
        gen["responseMimeType"] = "application/json"

    # 「長く考えすぎて時間切れ」を防ぐため、考える量を最小にする(モデルによって指定方法が違う)
    m = model.lower()
    thinking = None
    if "2.5" in m:
        thinking = {"thinkingBudget": 0}
    elif "gemini-3" in m:
        thinking = {"thinkingLevel": "low"}
    attempts = ([thinking] if thinking else []) + [None]   # 拒否されたら、指定なしでやり直す

    url = cfg["url"].format(model=urllib.parse.quote(model.strip()))
    data = None
    for i, th in enumerate(attempts):
        g = dict(gen)
        if th:
            g["thinkingConfig"] = th
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": g}
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key.strip()},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 400 and th and i < len(attempts) - 1:
                continue
            try:
                detail = json.loads(e.read().decode("utf-8"))["error"]["message"]
            except Exception:
                detail = str(e)
            hints = {
                400: "APIキーが正しくない可能性があります。キーをもう一度確認してください。",
                403: "このAPIキーでは使えない設定になっています。キーを確認してください。",
                404: "AIモデル名が見つかりません。「くわしい設定」でモデル名を変えてみてください。",
                429: "使いすぎです。少し待ってからもう一度お試しください。",
            }
            raise RuntimeError(f"{hints.get(e.code, 'AIとの通信でエラーが起きました。')}"
                               f"\n\n(詳細: {e.code} {detail})")
        except (socket.timeout, TimeoutError) as e:
            raise RuntimeError(_timeout_message()) from e
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                raise RuntimeError(_timeout_message()) from e
            raise RuntimeError("Googleのサーバーにつながりませんでした。\n"
                               "インターネット接続や、会社・学校のネットの制限(プロキシ)を確認してください。\n\n"
                               f"(詳細: {e.reason})") from e

    cands = data.get("candidates") or []
    if not cands:
        reason = (data.get("promptFeedback") or {}).get("blockReason", "")
        raise RuntimeError("AIが答えを返せませんでした。" + (f"(理由: {reason})" if reason else ""))
    parts = (cands[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if not text.strip():
        raise RuntimeError("AIから文章が返ってきませんでした。もう一度お試しください。")
    return text


def _timeout_message():
    return ("AIからの返事が時間内に届きませんでした(タイムアウト)。\n\n"
            "次のことを試してみてください。\n"
            "1. もう一度ボタンを押す(混み合っているだけのことがあります)\n"
            "2. 文章を短くする\n"
            "3. 「くわしい設定」で軽いモデル(名前に flash や flash-lite が付くもの)に変える\n"
            "4. インターネット接続を確認する。会社・学校のネットだと、Googleへの通信が"
            "制限されていることがあります")


def parse_telop_list(raw):
    """AIの返事(JSON配列のはず)を、文字列のリストにする。失敗したら行ごとに分ける。"""
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s).strip()
    try:
        data = json.loads(s)
        if isinstance(data, list):
            out = [str(x).strip() for x in data]
            if any(out):
                return out
    except Exception:
        pass
    return [ln.strip() for ln in s.splitlines() if ln.strip()]


def generate_telops(api_key, model, text, count, length, extra=""):
    """文章を、写真の枚数ぶん(count個)のテロップにまとめる。

    戻り値: (テロップのリスト(長さは必ず count), 注意メッセージ(なければ空文字))
    """
    prompt = build_telop_prompt(text, count, length, extra)
    items = parse_telop_list(call_gemini(api_key, model, prompt, json_mode=True))
    note = ""
    if len(items) > count:
        note = f"AIが{len(items)}個返したので、先頭の{count}個を使いました。"
        items = items[:count]
    elif len(items) < count:
        note = f"AIが{len(items)}個しか返さなかったので、残りの{count - len(items)}枚は文字なしです。"
        items += [""] * (count - len(items))
    return items, note
