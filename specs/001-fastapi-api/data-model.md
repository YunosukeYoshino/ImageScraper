# Data Model (Phase 1)

## Entities

### ScrapeRequest (input)
- url: string (required, http/https)
- output_dir: string (default: "./images")
- respect_robots: boolean (default: true)
- upload_to_drive: boolean (default: false)
- drive_folder_id: string | null (optional)

Validation:
- url must be a valid URL (http/https)
- output_dir must be a safe relative/absolute path
- if upload_to_drive==true and service account is not configured -> 400

### ScrapeSummary (output)
- saved: integer (>=0)
- failed: integer (>=0)
- output_dir: string
- uploaded: integer | null
- warnings: string[] (optional)
- errors: string[] (optional)
- files: string[] (optional; saved file paths)

### ErrorResponse
- code: integer (HTTP status)
- message: string
- details: any (optional)

## Relationships
- API -> Library: APIは `src/lib/image_scraper.py` の `scrape_images` を呼ぶ。
- Drive連携は `_init_drive` を内部で利用（必要時）。

## State Transitions
- Request受領 -> robotsチェック (respect_robots=true時) -> 画像URL抽出 -> ダウンロード -> （任意）Driveアップロード -> サマリー作成
- 途中エラー: 400/403/500 にマップし、ErrorResponseを返却
