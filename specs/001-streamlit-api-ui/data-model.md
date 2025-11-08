# Data Model: APIリクエストUI

**Feature**: 001-streamlit-api-ui

## Entities

### Request
- base_url: string (required) - 同一オリジン内APIのベースURL
- method: enum [GET, POST, PUT, PATCH, DELETE] (required)
- path: string (required) - 先頭にスラッシュ
- query: map<string,string> (optional)
- headers: map<string,string> (optional) - 機微情報はマスク保存
- body_json: string (optional) - JSONテキスト（検証必須）
- timeout_sec: number (optional, default: 30)

Validation:
- path は `/` で開始
- body_json がある場合は strict JSON としてパース可能であること
- timeout は 1〜120 秒

### Response
- status: number (required)
- duration_ms: number (required)
- body_type: enum [json, text, other] (required)
- body_preview: string (optional) - 大きい場合は先頭一部
- error_category: enum [none, input, network, server] (required)
- error_message: string (optional)

### Preset
- name: string (required, unique within UI)
- description: string (optional)
- method: enum [GET, POST, PUT, PATCH, DELETE] (required)
- path: string (required)
- sample_body_json: string (optional)
- notes: string (optional)

## Relationships
- Preset → Request: プリセットはRequestの初期値生成に用いる（送信時に上書き可能）

## Derived/Computed
- full_url = base_url + path + (query)
- response.body_type は Content-Type から推定
- response.body_preview はサイズ閾値でトリミング表示
