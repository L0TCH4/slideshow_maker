"""
★ ステップ(画面)の並び順 ★

下の STEP_CLASSES の順番どおりに、画面が1つずつ表示されます。
  ・順番を変える … 行を入れ替える
  ・ステップをなくす … その行を消す(例: AIを使わないなら AIGenerateStep を消す)
  ・新しいステップを足す … base.py の Step を継承したクラスを作って、ここに追加する
"""
from .ai_generate import AIGenerateStep
from .export import ExportStep
from .photos import PhotosStep
from .review import ReviewStep
from .source_text import SourceTextStep
from .video_settings import VideoSettingsStep

STEP_CLASSES = [
    PhotosStep,          # 1. 写真を選ぶ
    SourceTextStep,      # 2. 伝えたい文章を書く
    AIGenerateStep,      # 3. AIに考えてもらう
    ReviewStep,          # 4. テロップを確認する
    VideoSettingsStep,   # 5. 動画の設定
    ExportStep,          # 6. 動画を作る
]
