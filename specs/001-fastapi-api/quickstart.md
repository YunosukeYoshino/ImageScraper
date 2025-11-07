# Quickstart: FastAPI サーバ

## 前提
- Python 3.11
- uv がセットアップ済み (`pip install uv` など)

## 依存インストール
```bash
uv sync
uv add fastapi uvicorn[standard]
# Drive機能を使う場合
uv pip install .[drive]
```

## 実行
（後で `src/api/app.py` を追加予定）
```bash
uv run uvicorn src.api.app:app --reload --port 8000
```

## エンドポイント
- `GET /healthz` -> { "status": "ok" }
- `POST /scrape` -> 画像収集サマリー JSON

### POST /scrape リクエスト例
```json
{
  "url": "https://example.com",
  "output_dir": "./images",
  "respect_robots": true,
  "upload_to_drive": false
}
```

### レスポンス例（成功）
```json
{
  "saved": 12,
  "failed": 0,
  "output_dir": "./images",
  "files": ["images/abc123.png", "images/def456.jpg"]
}
```

### エラー例（robots不許可）
```json
{
  "code": 403,
  "message": "robots.txt disallows scraping for this URL"
}
```

## テスト
```bash
uv run python -m unittest discover -s tests/unit -p 'test_api.py'
```

## 次ステップ
- `src/api/app.py` & `schemas.py` 実装
- APIユニットテスト追加
- OpenAPI自動生成確認
