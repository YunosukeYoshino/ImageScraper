# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

image-saverは、Webページから画像をスクレイピングしてローカル保存し、オプションでGoogle Driveへアップロードできるツールです。トピック（検索ワード）からの自律的な画像探索機能（プロベナンス記録付き）も備えています。

**アーキテクチャ**: Python 3.11+ / uv管理（`pyproject.toml`）

**エントリポイント**:
- **ライブラリ**: `src/lib/image_scraper.py`
- **CLI**: `python -m src.cli.scrape_images`
- **FastAPI**: `src/api/app.py`
- **Streamlit UI**: `src/ui/image_scraper_app.py`

## Development Commands

```zsh
# セットアップ
uv sync
uv pip install .[drive]  # Google Drive機能（オプション）

# 実行
uv run streamlit run src/ui/image_scraper_app.py      # UI
uv run uvicorn src.api.app:app --reload --port 8000   # API
uv run python -m src.cli.scrape_images --url URL      # CLI
uv run python -m src.cli.scrape_images --topic "検索ワード" --limit 50  # トピック探索

# テスト
uv run python -m unittest discover -s tests/unit
uv run python -m unittest discover -s tests/unit -v   # 詳細出力
```

## Architecture

### ディレクトリ構成
- `src/lib/` - コアロジック（詳細: `src/lib/README.md`）
  - `domain/` - ドメイン層（エンティティ、ビジネスロジック、リポジトリIF）
  - `infrastructure/` - インフラ層（HTTP、パーサー、ストレージ、検索）
  - `application/` - アプリケーション層（ユースケース、横断的サービス）
- `src/api/` - FastAPI
- `src/ui/` - Streamlit UI（詳細: `src/ui/README.md`）
- `src/cli/` - CLIエントリポイント
- `tests/unit/` - ユニットテスト（モック使用、実ネットワーク接続なし）
- `discovery_logs/` - トピック探索のクエリログ
- `.specify/` - プロジェクト仕様・憲章

### Key Patterns
- **Clean Architecture**: domain → application → infrastructure の依存方向
- **CLI Contract**: 引数→stdout（JSON）、エラー→stderr + 非ゼロ終了
- **robots.txt**: ページ・画像両方で厳密に尊重（デフォルト有効）
- **ファイル命名**: URLのSHA-256ハッシュ + 拡張子
- **関連性スコアリング**: alt属性(0.4)/ファイル名(0.3)/周囲テキスト(0.2)/ドメイン信頼度(0.1)

## Constitution

本プロジェクトは `.specify/memory/constitution.md` (v1.1.0) に従います。

## Working with Code

- **テストファースト**: 実装前に`tests/unit/`にテストを追加
- **モック使用**: テストでは実ネットワーク接続を避ける
- **シークレット**: サービスアカウントJSON等は絶対にコミットしない（環境変数で参照）

## MCP Server Usage

利用可能なMCPサーバーがある場合、コード検索・パターンマッチングに優先使用

## Notes

- uvで管理（`package.json`なし）
- FastAPI OpenAPI: http://localhost:8000/docs
