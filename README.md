# Image Scraper

Webページから画像URLを収集し、プレビュー/選択/並列ダウンロードでローカル保存、必要に応じてGoogle Driveへアップロードできるツールです。Streamlit UI と FastAPI/CLI を用意しています。

- スクレイピング: requests + BeautifulSoup
- 画像保存: ローカルディレクトリ（デフォルト `./images`）
- ユーザーPCへZIPダウンロード: Streamlit UI から一括ダウンロード
- 並列ダウンロード + 進捗バー: UI から利用可能
- Google Drive アップロード: サービスアカウント (任意)
- パッケージ管理: uv (推奨)

> メモ: Google Drive への「認証不要」アップロード手段はありません。少なくとも一度の認証/資格情報設定が必須です。

## セットアップ (uv 必須)

macOS (zsh) での想定です。uv が未インストールの場合は以下から導入してください。

```zsh
# uv インストール (Homebrew 経由)
brew install uv
# もしくは公式インストーラ
curl -LsSf https://astral.sh/uv/install.sh | sh
```

プロジェクト依存のインストール:

```zsh
# プロジェクトルートで
uv sync
# (Drive 連携も使う場合はオプション依存を追加)
uv pip install .[drive]
```

以降は uv 経由で実行します。

## 使い方

### Streamlit UI（URLを入れてプレビュー→選択→保存/ZIPダウンロード）

```zsh
uv run streamlit run src/ui/image_scraper_app.py
```

できること:
- URLを入力してプレビュー（ダウンロードせず画像URLを抽出）
- 検索（URL/ファイル名の部分一致）
- ページング（ページサイズ: 10/25/50/100）
- 全選択/全解除トグル（表示中のページに対して）
- 並列ダウンロード（内部8ワーカー）+ 進捗バー表示
- 保存後の画像をギャラリー表示（5カラム）
- ZIPを作成し「ユーザーPCにダウンロード」

注意:
- robots.txt を既定で尊重します（ブロック時は警告）
- ZIPは保存済みファイルから作成されます

### CLI での画像ダウンロード (ローカルのみ)

```zsh
uv run python -m src.cli.scrape_images \
  --url https://example.com
  # 出力先はデフォルトで ./images に保存されます
```

### トピック（検索ワード）からの自律探索プレビュー（MVP）

```zsh
uv run python -m src.cli.scrape_images \
  --topic "富士山 紅葉" \
  --limit 50
```

現時点ではプレビュー JSON（プロベナンス含む）の出力が中心です。順次、フィルタ・選択ダウンロードや複数トピック対応を追加します。

### Google Drive にもアップロード (任意)

1. Google Cloud Console でサービスアカウントとキー(JSON)を作成
2. 対象フォルダIDを取得 (URLの `folders/<ID>` 部分)
3. そのフォルダをサービスアカウントメールに共有

```zsh
export GDRIVE_SA_JSON=path/to/service_account.json
uv run python -m src.cli.scrape_images \
  --url https://example.com \
  --out images \
  --drive-folder-id <your_folder_id>
# または明示指定
uv run python -m src.cli.scrape_images \
  --url https://example.com \
  --out images \
  --drive-folder-id <your_folder_id> \
  --drive-sa-json path/to/service_account.json
```

## テスト実行

まず依存を同期しておきます。

```zsh
uv sync
```

すべてのユニットテスト（`tests/unit` 配下）を実行:

```zsh
uv run python -m unittest discover -s tests/unit
```

詳細ログ（verbose）で実行:

```zsh
uv run python -m unittest discover -s tests/unit -v
```

特定のテストファイルのみ実行（例: API テスト）:

```zsh
uv run python -m unittest tests.unit.test_api
```

特定のテストケースのみ実行（クラス/メソッドを指定）:

```zsh
uv run python -m unittest tests.unit.test_api.TestAPI.test_healthz
```

メモ:
- テストは実ネットワークを利用しないようモック化しています。
- 一部テストは `./.tmp_test_out/` に一時ファイルを作成します。不要になれば削除して構いません。
 - Streamlit アプリは `import` のスモーク時に警告を出すことがあります（`streamlit run` で実行すれば問題ありません）。

## FastAPI API サーバの利用

FastAPI によるHTTP APIも利用できます（OpenAPIドキュメント: /docs）。

```zsh
# 依存を同期
uv sync

# サーバ起動（開発用）
uv run uvicorn src.api.app:app --reload --port 8000
```

エンドポイント:
- GET /healthz -> { "status": "ok" }
- POST /scrape -> リクエスト例:

```json
{
  "url": "https://example.com",
  "output_dir": "./images",
  "respect_robots": true,
  "upload_to_drive": false
}
```

レスポンス例:

```json
{
  "saved": 12,
  "failed": 0,
  "output_dir": "./images",
  "files": ["images/abc123.png", "images/def456.jpg"]
}
```

## 注意点 / ベストプラクティス

- robots.txt とサイト規約を厳密に尊重します（ページ・画像URLともに不許可はスキップ/中止）。
- 過剰な負荷を避け、レート制限・リトライ実装を活用してください。
- 公開配布物に含めたくない資格情報(JSON)はコミットしないでください。
 - 画像の著作権/利用規約を必ず確認の上、適切な範囲で利用してください。

## 構成

- `src/lib/image_scraper.py`: コア機能 (取得、解析、保存、Drive アップロード、プレビュー/並列ダウンロード)
- `src/lib/ui_helpers.py`: UI補助（JSON検証、URL構築、設定保存/読込、レスポンス要約）
- `src/cli/scrape_images.py`: CLI エントリポイント
- `src/ui/image_scraper_app.py`: Streamlit UI（プレビュー/検索/ページング/選択/並列ダウンロード/ZIP）
- `tests/unit/test_parse_images.py`: 最小ユニットテスト
 - `tests/unit/test_list_and_download_images.py`: プレビュー・選択ダウンロードのテスト
 - `tests/unit/test_parallel_download.py`: 並列ダウンロードと進捗のテスト

