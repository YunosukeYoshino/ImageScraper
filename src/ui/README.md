# src/ui - Streamlit UI

画像スクレイパーのStreamlit UIアプリケーション。

## 実行方法

```zsh
uv run streamlit run src/ui/image_scraper_app.py
```

## UI Conventions

- **グリッド**: 5カラムグリッド、`width="stretch"`（`use_container_width`は非推奨）
- **フロー**: URLプレビュー → 選択 → 並列ダウンロード → ZIPダウンロード
- **robots.txt**: 常に尊重

## 機能

- URL指定による画像プレビュー
- チェックボックスによる画像選択
- 並列ダウンロード（スレッドプール使用）
- 選択画像のZIPアーカイブ生成・ダウンロード
