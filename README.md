# Image Scraper

Webページから画像URLを収集しダウンロード、必要に応じてGoogle Driveへアップロードするシンプルなツールです。

- スクレイピング: requests + BeautifulSoup
- 画像保存: ローカルディレクトリ
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

### 画像のダウンロード (ローカルのみ)

```zsh
uv run python -m src.cli.scrape_images \
  --url https://example.com
  # 出力先はデフォルトで ./images に保存されます
```

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

## 構成

- `src/lib/image_scraper.py`: コア機能 (取得、解析、保存、Drive アップロード)
- `src/cli/scrape_images.py`: CLI エントリポイント
- `tests/unit/test_parse_images.py`: 最小ユニットテスト

