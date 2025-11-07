# Implementation Plan: FastAPI化（Web API 追加）

**Branch**: `001-fastapi-api` | **Date**: 2025-11-07 | **Spec**: /specs/001-fastapi-api/spec.md
**Input**: Feature specification from `/specs/001-fastapi-api/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

既存のスクレイパーライブラリ/CLIを温存しつつ、FastAPIでHTTP APIを追加する。`POST /scrape` でURLを受け取り、画像保存と（任意）Driveアップロードを実行し、CLIと整合的なJSONサマリーを返す。`GET /healthz` を提供し、OpenAPIドキュメント（/docs, /openapi.json）を自動生成する。

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, uvicorn[standard], pydantic（FastAPI経由）  
**Storage**: ローカルファイル（`./images`）。Driveは任意連携（既存の `[drive]` extras）  
**Testing**: unittest（既存に合わせる）＋ FastAPI TestClient  
**Target Platform**: Linux/macOS サーバ  
**Project Type**: Single project（`src/api` 追加）  
**Performance Goals**: 単一URLの処理 <2s p95（憲法の性能目安に準拠）  
**Constraints**: robots尊重、リトライ/バックオフ、観測性（logging）を維持  
**Scale/Scope**: 低〜中負荷前提（高度な並列は将来拡張）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle 1（Library-First）: APIは薄いラッパーとし、`src/lib/image_scraper.py` を直接呼び出す。OK
- Principle 2（CLI & Text）: 既存CLIは維持し、APIは追加インターフェース。OK
- Principle 3（Test-First）: APIの入出力・エラーマッピングのユニットテストを先行追加。OK
- Principle 4（Boundary Safety）: 既存のネットワーク/Drive境界のリトライ・ロギングを踏襲。API層でHTTPエラーへ変換。OK
- Principle 5（Observability）: API開始/終了ログ、失敗時のWARNING/ERRORを追加。OK

Gate Result: PASS（違反なし）

Post-Design Re-check: PASS（設計追加により新たな違反なし）

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/
├── api/
│   ├── app.py              # FastAPIアプリ本体（エンドポイント定義）
│   └── schemas.py          # Pydanticリクエスト/レスポンスモデル
├── cli/
│   └── scrape_images.py    # 既存CLI
└── lib/
  └── image_scraper.py    # 既存ロジック

tests/
├── unit/
│   ├── test_parse_images.py   # 既存
│   └── test_api.py            # APIの入出力とエラーハンドリング
└── contract/                  # （将来）OpenAPI契約テスト
```

**Structure Decision**: Single project。既存 `src/lib` を中核に `src/api` を追加し、テストは `tests/unit` に最小追加。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| （該当なし） | — | — |
