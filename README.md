# スライドショー動画メーカー

写真を選んで文章を書くと、AI(Gemini)がテロップを作り、MP4のスライドショー動画を自動で作ります。
画面は **6つのステップ** を1つずつ進めるだけです。

| ステップ | 内容 |
|---|---|
| 1 写真を選ぶ | 追加(ドラッグ&ドロップ対応)・並べ替え・削除 |
| 2 伝えたい文章を書く | 全部の写真ぶんの内容を、まとめて1つの文章で書く |
| 3 AIに考えてもらう | 文章を「写真の枚数ぶんのテロップ」に分けてまとめる |
| 4 テロップを確認する | 写真ごとに手直し / 文字の高さ・大きさ・動画の形を調整 |
| 5 動画の設定 | 全体の設定(長さ・ズーム・フォント・文字色・BGM)と、**写真ごとの設定(長さ・フォント・文字色)** |
| 6 動画を作る | MP4を書き出す(中止もできます) |

## 動かし方

```
pip install -r requirements.txt
python main.py
```

- Python 3.9 以上(Tkinter 付き)。ffmpeg は `imageio-ffmpeg` に同梱です。
- `tkinterdnd2` が入っていないときも動きます(ドラッグ&ドロップだけ使えません)。
- AIを使うには Gemini の APIキー(Google AI Studio で無料で作成)が必要です。
  画面の「このパソコンに保存する」にチェックすると `~/.slideshow_maker.json` に保存されます。
  環境変数 `GEMINI_API_KEY` に入れておくこともできます。

## 自動保存と「前回の続き」

- 編集内容(写真の一覧・文章・テロップ・写真ごとの設定・動画の設定)は、**3秒ごとに自動で保存**されます(変更があったときだけ)。
  閉じるときにも保存します。入力の途中(文章欄に書いている最中)の内容も保存されます。
- 次に起動すると、前回の内容が復元された状態で、**必ずステップ1の画面から**始まります。
  ステップ1に「前回の続きから始めています」と案内が出ます。写真のファイルが移動・削除されていたら、その写真だけ除きます。
- 保存先は、ホームフォルダの `.slideshow_maker_session.json` です(APIキーなどの設定は別ファイル `.slideshow_maker.json`)。
- ステップ1の赤い **「すべてリセットする」** ボタンで、写真・文章・テロップ・動画の設定を最初の状態に戻せます(確認が出ます)。
  APIキーとモデル名は消えません。
- 最後の画面の「最初からやり直す」は、写真と文章だけを消します(動画の設定は残ります)。

## ステップ5: 全体の設定と、写真ごとの設定

- **全体の設定**: 1枚の長さ・フォント・文字の色・ズーム・BGM。すべての写真に使われます。
- **写真ごとの設定**: 一覧から写真を選び、「この写真の長さ/フォント/文字の色を変える」にチェックを入れると、その写真だけ上書きできます。
  チェックしない項目は全体の設定に従います(全体を変えると、個別設定のない写真は一緒に変わります)。
  一覧の★は、個別設定がある写真です。「全体の設定に戻す」ボタンで元に戻せます。
- 写真の長さが違っても、切り替え(フェード)は自動でつながります。
- 暗い文字色を選んだときは、読みやすいように帯とフチが自動で白くなります(`TELOP_STYLE["auto_contrast"]` で切り替え)。
- データの持ち方: 個別設定は `Photo`(`app/state.py`)の `duration` / `font_path` / `text_color` に入ります。
  「個別設定がなければ全体」のルールは `AppState.duration_for / font_for / color_for` にまとまっています。

## 画面の大きさについて

- ウィンドウを小さくしても、各ステップが自動でスクロールになり、「戻る/次へ」は常に見えます。
- 幅が狭いと2列の画面は縦並びに、高さが低いと説明文は隠れます。
- 右上の「文字 小/大」、または `Ctrl` + `+` / `-` / `0` で、文字の大きさを変えられます(次回も覚えています)。

## フォルダ構成

```
main.py                    起動ファイル
requirements.txt
app/
  config.py                ★ 見た目・初期値・数値・AI設定(まずここを見る)
  prompts.py               ★ AIへの指示文(プロンプト)
  state.py                 写真・文章・設定値をまとめて持つ場所
  settings_store.py        APIキーなどの「設定」の保存/読み込み
  session_store.py         編集内容(前回の続き)の自動保存/復元
  core/                    画面に依存しない処理(単体でも使える)
    render.py              写真+テロップの描画 / ズーム効果
    video.py               動画の書き出し(ffmpeg)
    gemini.py              Gemini API との通信
    files.py               画像ファイルの収集
    fonts.py               使えるフォントの一覧
  ui/
    launcher.py            起動処理(ウィンドウ・フォント・ウィザードの組み立て)
    wizard.py              ステップを1つずつ見せる枠(上バー・戻る/次へ)
    widgets.py             スクロール枠・折り返し文字・2列⇔縦並び・プレビュー
    fields.py              フォント選択・文字色選択の入力部品
    style.py               フォントと色
    background.py          時間のかかる処理を裏で動かす道具
    dnd.py                 ドラッグ&ドロップ
    steps/
      __init__.py          ★ ステップの並び順
      base.py              ステップのひな形
      photos.py / source_text.py / ai_generate.py
      review.py / video_settings.py / export.py
```

## こんなときは、ここを変える

| やりたいこと | 変える場所 |
|---|---|
| 画面の文字を大きく/小さく(初期値) | `config.py` の `UI_FONT_SIZE` |
| 色(ボタン・見出し)を変える | `config.py` の `COLORS` |
| 起動時のウィンドウの大きさ、最小サイズ | `config.py` の `WINDOW_DEFAULT_SIZE` / `WINDOW_MIN_SIZE` |
| 2列→縦並びになる幅 | `config.py` の `LAYOUT_BREAKPOINT` |
| 動画の形(サイズ)を足す/消す | `config.py` の `SHAPES` |
| 1枚の秒数・ズーム・FPS などの初期値 | `config.py` の `DEFAULTS` |
| ズームの強さ | `config.py` の `KB_ZOOM` |
| 文字色の初期値 | `config.py` の `DEFAULTS["text_color"]` |
| 自動保存をやめる / 保存の間隔 / 保存先 | `config.py` の `AUTOSAVE_ENABLED` / `AUTOSAVE_INTERVAL_MS` / `SESSION_PATH` |
| 自動保存・リセットの対象にする設定値を増やす | `state.py` の `AppState.SETTING_KEYS`(と `default_settings()`) |
| 保存する項目(写真ごとの項目など)を増やす | `state.py` の `to_session()` と `load_session()` |
| 文字色のワンクリック候補を増減 | `config.py` の `TEXT_COLOR_PRESETS` |
| フォント一覧に出すフォントを増やす | `config.py` の `FONT_CANDIDATES`(パスを足す)と `FONT_LABELS`(表示名) |
| 暗い文字色での帯・フチの自動切り替え | `config.py` の `TELOP_STYLE["auto_contrast"]` |
| 写真ごとに変えられる項目を増やす | `state.py` の `Photo` に項目を足し、`ui/steps/video_settings.py` に入力欄を足す |
| テロップの色・帯・余白・フチ | `config.py` の `TELOP_STYLE` |
| 画質・書き出しの速さ | `config.py` の `VIDEO_ENCODE`(`crf` が小さいほど高画質) |
| AIモデル・待ち時間 | `config.py` の `GEMINI` |
| AIの口調・テロップのルール | `prompts.py` の `TELOP_PROMPT` |
| ステップの順番を入れ替える/消す | `ui/steps/__init__.py` の `STEP_CLASSES` |
| 各ステップの見出し・説明文・ボタン文言 | `ui/steps/○○.py` の `title` / `description` / `next_label` |

### 例: AIを使わない版にする
`ui/steps/__init__.py` の `STEP_CLASSES` から `SourceTextStep` と `AIGenerateStep` の行を消すだけです。
(テロップは「テロップを確認する」画面で、写真ごとに手入力できます。)

### 例: 新しいステップを足す
1. `ui/steps/base.py` の `Step` を継承したクラスを作り、`build()` に部品を置く。
2. `ui/steps/__init__.py` で import して `STEP_CLASSES` の好きな位置に追加する。

   ```python
   class MyStep(Step):
       title = "新しいステップ"
       description = "ここに説明"
       def build(self, body):
           ttk.Label(body, text="こんにちは").grid(row=0, column=0)
   ```
   値の受け渡しは `self.state`(`state.py`)を使います。必要なら `state.py` に変数を足してください。
   `on_show()` / `on_hide()` / `can_go_next()` で、表示・退出・「次へ」前のチェックができます。

### 例: AIを別のサービスに変える
`core/gemini.py` の `generate_telops(...)` が「(テロップのリスト, 注意メッセージ)」を返す形のまま、
中身を別のAPI呼び出しに差し替えれば、画面側は変更不要です。

## うまくいかないとき

- **テロップが「□」になる** → ステップ5の「フォント」で、日本語対応のフォントを選ぶ(「ファイルから選ぶ」で .ttf/.ttc も指定できます)。
- **AIが「モデルが見つかりません」/ タイムアウト** → ステップ3「くわしい設定」でモデル名を変える
  (例: `gemini-2.5-flash`)。それでも通らないときは、ネットの制限(会社・学校など)も疑ってください。
- **動画が作れない(ffmpeg)** → `pip install imageio-ffmpeg` をやり直す。
