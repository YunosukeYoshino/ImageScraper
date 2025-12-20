# Image Scraper

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/package%20manager-uv-blueviolet)](https://github.com/astral-sh/uv)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)

Webページから画像を収集し、ローカル保存やGoogle Driveへのアップロードができるツールです。トピック（検索ワード）からの自律的な画像探索機能も備えています。

## Features

- **マルチインターフェース** — CLI、FastAPI、Streamlit UIの3つの入口から同一のコア機能を利用
- **トピック探索** — キーワードから自律的に画像を発見し、プロベナンス（出典情報）付きで管理
- **関連性スコアリング** — alt属性・ファイル名・周囲テキストから関連度を自動計算（高🟢/中🟡/低🔴）
- **並列ダウンロード** — 8ワーカーによる高速ダウンロードと進捗表示
- **robots.txt準拠** — ページ・画像URLともに自動でアクセス制限を尊重
- **Google Drive連携** — rclone（個人向け）またはサービスアカウント（自動化向け）に対応
- **解像度フィルタ** — 最小幅・高さでの画像フィルタリング
- **ドメイン制御** — 許可/拒否リストによる取得元制限

## Prerequisites

- Python 3.11以上
- [uv](https://github.com/astral-sh/uv) — パッケージマネージャ
- rclone（Google Drive連携を使う場合、オプション）

## Getting Started

### インストール

```bash
# uv のインストール（未導入の場合）
brew install uv
# または
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存パッケージの同期
uv sync

# Google Drive機能を使う場合（オプション）
uv pip install .[drive]
```

### クイックスタート

<details>
<summary><b>Streamlit UI（推奨）</b></summary>

```bash
uv run streamlit run src/ui/image_scraper_app.py
```

ブラウザで開き、URLまたはトピックを入力して画像を探索・ダウンロードできます。

**主な機能:**
- 画像プレビュー（ダウンロード前に確認）
- 関連性フィルタ（高/中/低でスコア絞り込み）
- 検索フィルタ（URL/ファイル名で絞り込み）
- ページネーション（10/25/50/100件表示）
- 選択ダウンロード + ZIPエクスポート
- 5カラムギャラリー表示

</details>

<details>
<summary><b>CLI</b></summary>

```bash
# URL指定でダウンロード
uv run python -m src.cli.scrape_images --url https://example.com

# トピック探索（プレビューのみ）
uv run python -m src.cli.scrape_images --topic "富士山 紅葉" --limit 50

# トピック探索 + フィルタ付きダウンロード
uv run python -m src.cli.scrape_images --topic "keyword" --download \
  --min-width 800 --min-height 600 \
  --allow-domain pixabay.com,unsplash.com
```

**出力形式:** JSON（stdout）、エラーはstderr

</details>

<details>
<summary><b>FastAPI</b></summary>

```bash
uv run uvicorn src.api.app:app --reload --port 8000
```

**エンドポイント:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | ヘルスチェック |
| POST | `/scrape` | 画像スクレイピング実行 |

OpenAPIドキュメント: http://localhost:8000/docs

**リクエスト例:**

```json
{
  "url": "https://example.com",
  "output_dir": "./images",
  "respect_robots": true
}
```

</details>

## Google Drive連携

> [!NOTE]
> Google Driveへの「認証不要」アップロード手段はありません。初回のみ認証設定が必要です。

### 方式1: rclone（個人利用向け）

個人のGoogle Driveアカウントを直接利用できます。

```bash
# インストール
brew install rclone  # macOS
# または
curl https://rclone.org/install.sh | sudo bash  # Linux

# 設定（ブラウザで認証）
rclone config

# 動作確認
rclone lsd gdrive:
```

<details>
<summary>rclone設定の詳細手順</summary>

1. `n` — 新しいリモート作成
2. Name: `gdrive`
3. Storage: `18` (Google Drive)
4. client_id, client_secret: Enterでスキップ
5. scope: `1` (Full access)
6. service_account_file: Enterでスキップ
7. Edit advanced config: `n`
8. Use web browser: `y` → ブラウザで認証
9. Configure as team drive: `n`
10. Confirm: `y`, Quit: `q`

</details>

**コードから利用:**

```python
from src.lib.drive_uploader import create_uploader

uploader = create_uploader(method="rclone", rclone_remote="gdrive")
```

### 方式2: サービスアカウント（自動化向け）

サーバー間認証が必要な場合に最適です。

1. Google Cloud Consoleでサービスアカウントを作成
2. JSONキーをダウンロード
3. 対象フォルダをサービスアカウントメールに共有

```bash
export GDRIVE_SA_JSON=path/to/service_account.json
uv run python -m src.cli.scrape_images \
  --url https://example.com \
  --drive-folder-id <folder_id>
```

## Testing

```bash
# 全テスト実行
uv run python -m unittest discover -s tests/unit

# 詳細出力
uv run python -m unittest discover -s tests/unit -v

# 特定テストのみ
uv run python -m unittest tests.unit.test_api
```

> [!TIP]
> テストはモック化されており、実際のネットワーク接続は発生しません。

## Project Structure

```
src/
├── lib/                    # コアライブラリ
│   ├── domain/             # ドメイン層（エンティティ、ビジネスロジック）
│   ├── infrastructure/     # インフラ層（HTTP、パーサー、ストレージ）
│   ├── application/        # アプリケーション層（ユースケース、サービス）
│   └── [レガシーモジュール] # 後方互換のため維持
├── cli/                    # CLIエントリポイント
├── api/                    # FastAPI サーバー
└── ui/                     # Streamlit UI
tests/
└── unit/                   # ユニットテスト
```

**主要モジュール:**

| Module | Description |
|--------|-------------|
| `image_scraper.py` | 画像取得・解析・保存のコアロジック |
| `topic_discovery.py` | トピックベースの自律探索 |
| `domain/services/relevance_scorer.py` | 画像の関連性スコアリング |
| `drive_uploader.py` | Google Driveアップロード（Strategy Pattern） |
| `application/services/rate_limiter.py` | トークンバケット方式のレート制限 |

## Best Practices

> [!IMPORTANT]
> - robots.txtとサイト規約を尊重してください
> - 過剰な負荷をかけないよう、適切なレート制限を設定してください
> - 画像の著作権・利用規約を確認の上、適切な範囲で利用してください
> - 認証情報（JSONキー等）をリポジトリにコミットしないでください
