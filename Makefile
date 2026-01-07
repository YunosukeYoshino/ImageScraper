# Makefile - image-saver 開発コマンド集
# 使い方: make help

.PHONY: help setup sync ui api test test-v lint format check clean scrape topic

# デフォルト: ヘルプ表示
.DEFAULT_GOAL := help

#==============================================================================
# セットアップ
#==============================================================================

setup: ## 初回セットアップ（依存関係 + pre-commit）
	uv sync --extra dev
	uv run pre-commit install

sync: ## 依存関係の同期
	uv sync

sync-drive: ## Google Drive機能付きで同期
	uv sync
	uv pip install .[drive]

#==============================================================================
# アプリケーション実行
#==============================================================================

ui: ## Streamlit UIを起動
	uv run streamlit run src/ui/image_scraper_app.py

api: ## FastAPI サーバーを起動（開発モード）
	uv run uvicorn src.api.app:app --reload --port 8000

#==============================================================================
# CLI（画像スクレイピング）
#==============================================================================

# 使用例:
#   make scrape URL=https://example.com
#   make scrape URL=https://example.com LIMIT=10 OUT=downloads
scrape: ## URLから画像をスクレイピング (URL=... [LIMIT=n] [OUT=dir])
ifndef URL
	@echo "エラー: URLを指定してください"
	@echo "使用例: make scrape URL=https://example.com"
	@exit 1
endif
	uv run image-scrape --url "$(URL)" $(if $(LIMIT),--limit $(LIMIT)) $(if $(OUT),--out $(OUT))

# 使用例:
#   make topic KEYWORD="富士山"
#   make topic KEYWORD="富士山" LIMIT=100
#   make topic-download KEYWORD="富士山" OUT=images
topic: ## トピック探索（プレビューのみ） (KEYWORD=... [LIMIT=n])
ifndef KEYWORD
	@echo "エラー: KEYWORDを指定してください"
	@echo "使用例: make topic KEYWORD=\"富士山\""
	@exit 1
endif
	uv run image-scrape --topic "$(KEYWORD)" $(if $(LIMIT),--limit $(LIMIT))

topic-download: ## トピック探索 + ダウンロード (KEYWORD=... [LIMIT=n] [OUT=dir])
ifndef KEYWORD
	@echo "エラー: KEYWORDを指定してください"
	@echo "使用例: make topic-download KEYWORD=\"富士山\" OUT=images"
	@exit 1
endif
	uv run image-scrape --topic "$(KEYWORD)" --download $(if $(LIMIT),--limit $(LIMIT)) $(if $(OUT),--out $(OUT))

#==============================================================================
# テスト・品質チェック
#==============================================================================

test: ## ユニットテストを実行
	uv run python -m unittest discover -s tests/unit

test-v: ## ユニットテストを実行（詳細出力）
	uv run python -m unittest discover -s tests/unit -v

lint: ## Ruff リントチェック
	uv run ruff check .

format: ## Ruff フォーマット
	uv run ruff format .

check: format lint test ## フォーマット + リント + テスト（コミット前推奨）

#==============================================================================
# ユーティリティ
#==============================================================================

clean: ## キャッシュ・一時ファイルを削除
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true

#==============================================================================
# ヘルプ
#==============================================================================

help: ## このヘルプを表示
	@echo ""
	@echo "image-saver 開発コマンド"
	@echo "========================"
	@echo ""
	@echo "使い方: make [ターゲット]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "例:"
	@echo "  make setup              # 初回セットアップ"
	@echo "  make ui                 # Streamlit UIを起動"
	@echo "  make api                # FastAPI サーバーを起動"
	@echo "  make scrape URL=https://example.com"
	@echo "  make topic KEYWORD=\"富士山\""
	@echo "  make check              # コミット前の品質チェック"
	@echo ""
