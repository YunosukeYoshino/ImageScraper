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

### Google Drive にもアップロード (任意)

Image Scraper は2つの Google Drive アップロード方式をサポートしています：

#### 方式1: rclone (推奨 - 個人 Drive 向け)

**特徴**:
- 個人 Google Drive アカウントを直接利用可能
- 初回のみブラウザ経由で OAuth 認証、以降は認証不要
- サービスアカウント作成が不要
- コマンドラインツールとして独立して動作

**セットアップ手順**:

1. rclone をインストール:

```zsh
# macOS
brew install rclone

# Linux
curl https://rclone.org/install.sh | sudo bash
```

2. rclone を設定:

```zsh
rclone config
```

設定手順:
1. `n` - 新しいリモート作成
2. Name: `gdrive`
3. Storage: `18` (Google Drive)
4. client_id: [Enter でスキップ]
5. client_secret: [Enter でスキップ]
6. scope: `1` (Full access)
7. service_account_file: [Enter でスキップ]
8. Edit advanced config: `n`
9. Use web browser: `y`
10. ブラウザで Google アカウント認証
11. Configure as team drive: `n`
12. Confirm: `y`
13. Quit: `q`

3. 動作確認:

```zsh
# Drive のフォルダ一覧を表示
rclone lsd gdrive:

# バックアップ用フォルダを作成（任意）
rclone mkdir gdrive:n8n-backups
```

4. Python コードから利用:

```python
from src.lib.image_scraper import scrape_images
from src.lib.drive_uploader import create_uploader

# rclone uploader を作成
uploader = create_uploader(method="rclone", rclone_remote="gdrive")

# 画像をスクレイプして Drive にアップロード
result = scrape_images(
    url="https://example.com",
    output_dir="./images",
    drive_uploader=uploader,
    drive_folder="n8n-backups"  # Drive 上のフォルダパス
)
```

**自動セットアップスクリプト**:

便利な自動セットアップスクリプトも利用できます：

```zsh
# scripts/setup_rclone.sh を実行
chmod +x scripts/setup_rclone.sh
./scripts/setup_rclone.sh
```

---

#### 方式2: サービスアカウント (バックエンド自動化向け)

**特徴**:
- サーバー間認証に最適（サーバーサイドアプリケーション向け）
- ユーザー操作不要で完全自動化が可能
- 複数環境・複数プロジェクトで同じ認証情報を再利用可能
- Google Cloud Console での初期設定が必要

**セットアップ手順**:

1. Google Cloud Console でサービスアカウントとキー(JSON)を作成
2. 対象フォルダIDを取得 (URLの `folders/<ID>` 部分)
3. そのフォルダをサービスアカウントメールに共有
4. Python コードから利用:

```python
from src.lib.image_scraper import scrape_images
from src.lib.drive_uploader import create_uploader

# Service account uploader を作成
uploader = create_uploader(
    method="service_account",
    service_account_file="path/to/service_account.json"
)

# 画像をスクレイプして Drive にアップロード
result = scrape_images(
    url="https://example.com",
    output_dir="./images",
    drive_uploader=uploader,
    drive_folder="your_folder_id"  # Drive フォルダ ID
)
```

**CLI から利用** (レガシー互換):

```zsh
export GDRIVE_SA_JSON=path/to/service_account.json
uv run python -m src.cli.scrape_images \
  --url https://example.com \
  --out images \
  --drive-folder-id <your_folder_id>
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

