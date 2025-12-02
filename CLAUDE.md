# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

image-saverは、Webページから画像をスクレイピングしてローカル保存し、オプションでGoogle Driveへアップロードできるツールです。トピック（検索ワード）からの自律的な画像探索機能（プロベナンス記録付き）も備えています。

**アーキテクチャ**: 単一のPythonプロジェクト（Python 3.11+）で、uvにより管理されています（`pyproject.toml`）。

**主要エントリポイント**:
- **ライブラリ**: `src/lib/image_scraper.py` - スクレイピング、ダウンロード、Drive連携
- **CLI**: `python -m src.cli.scrape_images` - JSON出力（URL指定またはトピック探索）
- **FastAPI**: `src/api/app.py` - HTTP API（/scrape、/healthz）
- **Streamlit UI**: `src/ui/image_scraper_app.py` - プレビュー／検索／選択／並列ダウンロード／ZIP

## Development Commands

### Environment Setup
```zsh
# プロジェクト依存のインストール
uv sync

# Google Drive機能を使う場合（オプション）
uv pip install .[drive]
```

### Running the Application
```zsh
# Streamlit UI（プレビュー・選択・並列ダウンロード・ZIP）
uv run streamlit run src/ui/image_scraper_app.py

# FastAPI サーバー（開発用）
uv run uvicorn src.api.app:app --reload --port 8000

# CLI（URLから画像をダウンロード）
uv run python -m src.cli.scrape_images --url https://example.com

# CLI（トピックから自律探索・プレビュー）
uv run python -m src.cli.scrape_images --topic "富士山 紅葉" --limit 50
```

### Testing
```zsh
# すべてのユニットテストを実行
uv run python -m unittest discover -s tests/unit

# 詳細ログ付き実行
uv run python -m unittest discover -s tests/unit -v

# 特定のテストファイルのみ実行
uv run python -m unittest tests.unit.test_api

# 特定のテストケースのみ実行（クラス/メソッド指定）
uv run python -m unittest tests.unit.test_api.TestAPI.test_healthz
```

## Architecture & Key Patterns

### Core Components
- **`src/lib/image_scraper.py`**: ネットワーク取得、HTML解析（BeautifulSoup）、画像ダウンロード、Drive連携。UI向けヘルパー（`list_images`、`download_images`、`download_images_parallel`）も提供
- **`src/lib/topic_discovery.py`**: トピック（検索ワード）から候補ページを自律的に探索し、プロベナンス記録を生成
- **`src/lib/search_provider.py`**: 検索プロバイダ（DuckDuckGo等）のラッパー。レート制限と再試行を実装
- **`src/lib/rate_limit.py`**: トークンバケット方式のレート制限（burst制御付き）
- **`src/lib/models_discovery.py`**: プロベナンスエントリ、クエリログ、プレビュー結果のデータモデル
- **`src/lib/ui_helpers.py`**: UI向けユーティリティ（JSON検証、URL構築、設定保存/読込）

### CLI Contract
- 引数 → stdout（JSON）またはテキスト出力
- エラー → stderr + 非ゼロ終了コード
- 非対話的（プロンプトなし）

### Robots.txt Compliance
- ページおよび画像URLの両方でrobots.txtを厳密に尊重
- ページ自体が不許可なら処理を中止、画像が不許可ならスキップ
- CLI/API: `--respect-robots` / `respect_robots` フラグで制御（デフォルトはTrue）

### Image Detection & Naming
- 画像検出: 代表的な拡張子の正規表現（`.jpg|.jpeg|.png|.gif|.webp|.svg`）+ パス末尾チェックのフォールバック
- ファイル命名: URLのSHA-256ハッシュ + 推定拡張子（衝突回避）

### Topic Discovery & Provenance (Principle 6)
トピックベースの探索では、以下のルールを厳守：
- **専用モジュール**: `src/lib/topic_discovery.py`に実装
- **再現可能なクエリログ**: `discovery_logs/` に保存（トピック、検索クエリ、タイムスタンプ）
- **レート制限**: 検索プロバイダごとに`src/lib/rate_limit.py`でバースト制御
- **robots.txt尊重**: 発見したすべてのページでスクレイピング前にチェック
- **プロベナンス記録**: 各画像に`source_page_url`、`image_url`、`discovery_method`、タイムスタンプを付与
- **テスト必須**: モック使用（CI中の実ネットワークアクセスなし）

### Google Drive Integration
- 追加依存グループ: `[drive]`（`google-api-python-client`、`google-auth`）
- サービスアカウントJSON（`GDRIVE_SA_JSON`環境変数または`--drive-sa-json`フラグ）が必要
- 対象フォルダに対するサービスアカウントの共有権限が必須

### Logging & Observability
- `logging` モジュールを使用（構造化またはレベル付きメッセージ）
- 保存/アップロード → INFO、失敗 → WARNING/ERROR
- 重要な操作（fetch、download、upload）の開始/終了を記録

## Constitution & Principles

本プロジェクトは `.specify/memory/constitution.md` (v1.1.0) で定義された6つの原則に従います：

1. **Library-First Modularity**: 新機能は独立してテスト可能な小モジュールとして`src/`配下に実装
2. **CLI & Text Interface**: CLI実行可能（`uv run python -m ...`）、引数→stdout、エラー→stderr
3. **Test-First Enforcement**: 非自明な機能は実装前にテストを作成（Red-Green-Refactor）
4. **External Boundary & Integration Safety**: ネットワーク/API境界にエラーハンドリング（タイムアウト、リトライ、ログ）
5. **Observability & Simplicity**: 構造化ログ、重複2回以上でリファクタ（早すぎる抽象化を避ける）
6. **Autonomous Topic Discovery & Provenance**: トピック探索では専用モジュール、再現可能ログ、レート制限、robots.txt尊重、プロベナンス記録、モックテスト

詳細は `.specify/memory/constitution.md` を参照してください。

## Working with Code

### Adding New Features
1. `src/` 配下に小さな独立モジュールとして実装
2. **テストファースト**: 実装前に`tests/unit/`にテストを追加
3. ネットワーク/Drive境界にはリトライとログを実装
4. テストではネットワークをモック化
5. CLIラッパーとライブラリ関数の両方を公開

### Streamlit UI Conventions
- 5カラムグリッド、`use_container_width=True`（`use_column_width`は非推奨）
- フロー: URLプレビュー → 選択 → 並列ダウンロード → ZIPダウンロード
- robots.txt尊重を徹底

### Credentials & Secrets
- **絶対にコミットしない**: サービスアカウントJSON、API キー等
- 環境変数（`GDRIVE_SA_JSON`）またはCLIフラグで参照

### Files & Directories
- `src/lib/`: コアロジック（スクレイピング、トピック探索、レート制限等）
- `src/api/`: FastAPI アプリケーション
- `src/ui/`: Streamlit UI
- `src/cli/`: CLIエントリポイント
- `tests/unit/`: ユニットテスト（実ネットワーク接続なし、モック使用）
- `discovery_logs/`: トピック探索の再現可能なクエリログ
- `.specify/`: プロジェクト仕様、憲章、テンプレート
- `specs/`: 機能仕様（各トピックごとのフォルダ）

## MCP Server Usage

### Serena MCP for Code Search

**コード検索にはSerena MCPを優先的に使用**:

- `/serena` コマンドで体系的なファイル整理とコード検索を実行
- ネイティブGrepツールよりもSerena MCPを優先してコードベース探索に使用
- Serenaはセマンティックなコード理解と構造化検索機能を提供
- 複数ファイルにまたがるパターンマッチングにSerenaを使用

**Serenaを使用すべき場面**:
- コードベース全体にわたるパターン検索
- 特定の関数、クラス、インポートの検索
- 体系的なファイル整理とクリーンアップ
- コード依存関係の理解

**例**:
```
/serena grep "import.*requests" to find all requests imports
/serena search for TODO comments across the project
/serena organize files by moving scripts to appropriate directories
```

## Notes

- 本プロジェクトはuvで管理されており、`package.json`は存在しません（Pythonプロジェクト）
- `./.tmp_test_out/` には一部テストが一時ファイルを作成します（削除可能）
- Streamlit アプリは`import`のスモークテスト時に警告を出すことがありますが、`streamlit run`で実行すれば問題ありません
- FastAPI の OpenAPI ドキュメント: http://localhost:8000/docs
