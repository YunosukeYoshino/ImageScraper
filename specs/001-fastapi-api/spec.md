# Feature Spec: FastAPI化 (Web API ラッパー)

## Summary

現行のライブラリ/CLI (`src/lib/image_scraper.py`, `src/cli/scrape_images.py`) を温存しつつ、FastAPI によるWeb APIを追加する。主目的はHTTP経由で同等機能（URLから画像を収集し保存、任意でGoogle Driveへアップロード）を提供すること。OpenAPI ドキュメントを自動生成し、非対話・JSON応答を基本とする。

## Goals
- HTTP APIで `scrape_images` を呼び出し可能にする。
- 入出力をJSONでやり取り（CLI契約と整合的なサマリー構造）。
- ロギング・リトライ・robots尊重など既存ポリシーを保持。
- OpenAPI（/docs, /openapi.json）を提供。

## Non-Goals
- 既存CLIの破壊的変更。
- 認証・レート制限の導入（将来の拡張とする）。

## User Stories
1. APIクライアントとして、URLをPOSTすればサーバが画像を保存し、結果サマリー（保存件数・失敗件数・出力先など）をJSONで返して欲しい。
   - Acceptance:
     - POST /scrape に `{ "url": "https://example.com", "output_dir": "images", "respect_robots": true, "upload_to_drive": false }` などを渡すと200でJSONを返す。
     - 保存ログはINFOで記録、失敗はWARNING/ERROR。
     - robots不許可時はHTTP 403相当のエラーJSON。
2. ヘルスチェックとして、サーバの稼働確認エンドポイントが欲しい。
   - Acceptance: GET /healthz が `{ "status": "ok" }` を返す。
3. （任意）Drive連携をAPI引数で制御可能にしたい。
   - Acceptance: service account JSONが設定済みなら、`upload_to_drive=true`でアップロードし、アップロード結果をサマリーに含める。

## Constraints
- Python >=3.11、uv/pyproject.tomlを使用。
- 追加依存: `fastapi`, `uvicorn[standard]`, `pydantic`（FastAPI依存でOK）。
- ネットワーク処理は既存ロジックを再利用し、API層では例外→HTTPエラー変換。
- 同時実行: FastAPIのデフォルト（スレッド）で可。重い処理は現行同期I/Oで問題ない規模。

## API Sketch
- GET /healthz -> 200 { status: "ok" }
- POST /scrape -> 200 { summary } or エラーコード（400/403/500）
  - Request JSON fields:
    - url: str (required)
    - output_dir: str = "./images"
    - respect_robots: bool = true
    - upload_to_drive: bool = false
    - drive_folder_id: Optional[str]

## Observability
- logging: 既存ロガーを再利用、APIレイヤーで開始/終了をINFOで出力。

## Rollout & Backward Compatibility
- 新規 `src/api/` を追加。既存CLIと共存。
- テスト: unitに追加（pydanticモデル、エラーハンドリング）、将来はcontract/integrationも。
