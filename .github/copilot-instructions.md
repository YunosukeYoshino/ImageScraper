# image-saver 用 Copilot 指示書

このドキュメントは、このリポジトリで AI コーディングエージェントが生産的に作業するための指針です。返答は簡潔にし、リポジトリの規約に従ってください。

## アーキテクチャと意図

- 単一の Python プロジェクトで、uv により管理されています（`pyproject.toml`）。中核ロジックは `src/` 配下にあります。
- 主機能: Web ページから画像をスクレイピングしてローカル保存。必要に応じてサービスアカウントを用いて Google Drive へアップロード可能。Streamlit UI を提供し、プレビュー／検索／選択／並列ダウンロードおよび ZIP での PC へのエクスポートをサポートします。
- 公開エントリポイント:
  - ライブラリ: `src/lib/image_scraper.py`（`scrape_images` と `_init_drive` をエクスポート。UI 向けヘルパーとして `list_images`、`download_images`、`download_images_parallel` も提供）
  - CLI: `python -m src.cli.scrape_images`（詳細は下記）
  - UI: `uv run streamlit run src/ui/image_scraper_app.py`
- テストは `tests/` 配下にあります（現状はユニットテストのみ）。

## 規約とパターン

- CLI の契約: 引数 → stdout（JSON サマリ）、エラー → stderr + 非ゼロ終了コード。
- ネットワーキング: requests を使用し、リトライ／バックオフを実装。パースには BeautifulSoup を使用。
- 画像検出: 代表的な拡張子の正規表現 + パス末尾チェックのフォールバック。
- ファイル命名: URL の SHA‑256 ハッシュ + 推定拡張子で衝突を回避。
- 可観測性: 保存／アップロードは INFO、失敗は WARNING/ERROR で `logging` 出力。
- Robots: robots.txt を厳密に尊重（ページ／画像 URL ともに不許可はスキップ。ページ自体が不許可なら中止）。
- Drive へのアップロード: 追加依存グループ `[drive]`。サービスアカウント JSON と共有フォルダ権限が必要。

## 主要ファイル

- `src/lib/image_scraper.py`: 取得、パース、ダウンロード、Drive アップロードのヘルパー。UI 向け `list_images`、`download_images`、`download_images_parallel` を提供。
- `src/lib/ui_helpers.py`: UI ユーティリティ（JSON 検証、ヘッダーのマスキング、URL ビルダー、設定の保存／読み込み、レスポンスの要約）。
- `src/cli/scrape_images.py`: CLI の引数解析。JSON サマリを出力。
- `src/ui/image_scraper_app.py`: プレビュー／検索／ページング／選択と、ZIP 付き並列ダウンロードを備えた Streamlit アプリ。
- `pyproject.toml`: uv のプロジェクト設定。必要に応じて `[drive]` をインストール。
- `README.md`: セットアップ（uv）、使用例、テスト実行コマンド。
- `.specify/memory/constitution.md`: プロジェクト規約（library-first、CLI、test-first、observability、統合の安全性）。

## ビルド・実行・テスト（macOS/zsh）

```zsh
# 環境セットアップ
uv sync
# （Drive 機能を使う場合）
uv pip install .[drive]

# スクレイパー実行（出力先はデフォルトで ./images）
uv run python -m src.cli.scrape_images --url https://example.com

# Streamlit UI 実行（プレビュー／検索／ページング／選択／並列 ZIP）
uv run streamlit run src/ui/image_scraper_app.py

# テスト
uv run python -m unittest discover -s tests/unit
```

## 実装のヒント（プロジェクト固有）

- 機能追加は `src/` 配下の小さなモジュールとして行い、まずテストを追加することを推奨。
- ネットワーク／Drive との境界に触れる場合は、リトライを入れ、失敗をログ化。テストではネットワークをモック。
- CLI は非対話的に保ち、プロンプトではなくフラグを追加する。出力先はデフォルトで ./images。
- 資格情報はコミットしない。環境変数（`GDRIVE_SA_JSON`）または CLI フラグで参照。
- 新しい連携を追加する場合は、ライブラリ関数と CLI ラッパーの両方を公開。
- UI 規約: Streamlit は 5 カラムグリッド、`use_container_width` を使用（`use_column_width` は非推奨）。「URL プレビュー → 選択 → 並列ダウンロード → ZIP ダウンロード」の流れ。robots.txt を尊重。

## 不明な場合

- `/.specify/memory/constitution.md` の原則に合わせる。
- 規約から外れる必要がある場合は、PR で理由を説明し、最小限のテスト／ログを追加。

## 使用技術

- Python 3.11 + FastAPI、uvicorn[standard]、pydantic（FastAPI 経由）（001-fastapi-api）
- ローカルファイル（`./images`）。Drive は任意連携（既存の `[drive]` extras）（001-fastapi-api）
- Python 3.11 + FastAPI（既存 API）、requests、BeautifulSoup、Streamlit（UI 層）（001-streamlit-api-ui）
- N/A（ローカルブラウザ保存のみ）（001-streamlit-api-ui）

## 最近の変更

- 001-fastapi-api: Python 3.11 + FastAPI、uvicorn[standard]、pydantic（FastAPI 経由）を追加。
- Streamlit UI: `src/ui/image_scraper_app.py` を追加。プレビュー／検索／ページング／選択、並列ダウンロード、ZIP エクスポートをサポート。
- ライブラリ: `list_images`、`download_images`、`download_images_parallel` を追加。`src/lib/ui_helpers.py` とユニットテストを追加。
