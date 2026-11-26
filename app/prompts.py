"""
★ AIへの指示文(プロンプト) ★

AIにどんなテロップを作らせるかは、ここの文章を書き換えるだけで変えられます。
{count} {length} {extra} {text} は、アプリが自動で埋める部分なので消さないでください。
"""

TELOP_PROMPT = """あなたは、写真スライドショー動画の字幕(テロップ)を作る編集者です。
下の【文章】は、これから作る動画で伝えたい内容です。
この内容の流れに沿って、ちょうど{count}個のテロップに分けてください。
(写真1枚につきテロップ1つを、順番どおりに使います)

ルール:
- 1つのテロップは、日本語で{length}文字前後にする
- 読みやすいように、1つのテロップの中で改行してもよい(最大3行くらい)
- 最初のテロップは導入、最後のテロップは締めくくりになるように流れを作る
- 【文章】に書かれていない事実は付け足さない
{extra}
出力は、{count}個の文字列だけを入れたJSON配列にしてください。
例: ["1枚目のテロップ", "2枚目のテロップ"]
前置きや説明は書かないでください。

【文章】
{text}
"""

# ユーザーが「AIへのお願い」を入力したときだけ、{extra} の場所に入る1行
EXTRA_LINE = "- 追加のお願い: {extra}\n"


def build_telop_prompt(text, count, length, extra=""):
    extra = extra.strip()
    extra_block = EXTRA_LINE.format(extra=extra) if extra else ""
    return TELOP_PROMPT.format(count=count, length=length, extra=extra_block, text=text.strip())
