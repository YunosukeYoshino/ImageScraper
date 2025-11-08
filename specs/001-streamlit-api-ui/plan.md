# Implementation Plan: APIリクエストUI

**Branch**: `001-streamlit-api-ui` | **Date**: 2025-11-08 | **Spec**: ./spec.md
**Input**: Feature specification from `/specs/001-streamlit-api-ui/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

社内 image-saver API を同一オリジンで手早く試験するためのブラウザUI（技術的には Streamlit 想定だが仕様は技術非依存）。単一リクエスト送信・共通接続設定のローカル永続化・プリセットによる定型操作短縮を提供し、レスポンスを整形表示・エラー分類表示する。Researchで対象範囲（内部API限定）・永続化（期限なしローカル）・配置（同一オリジン）を確定。シンプル構成（追加DBなし）で既存 FastAPI バックエンドに付随する UI 層を提供。

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI (既存API), requests, BeautifulSoup, Streamlit(UI層)  
**Storage**: N/A（ローカルブラウザ保存のみ）  
**Testing**: unittest（既存） + 追加でUIロジック分離した関数を単体テスト（JSONバリデーション等）  
**Target Platform**: macOS/Linux 開発環境 + ブラウザ  
**Project Type**: single project (library + API + UI)  
**Performance Goals**: 単一リクエスト結果表示 ≤3秒（既存API呼び出し+整形）  
**Constraints**: メモリ軽量（UIで大量保持しない）、外部API接続機能は追加しない  
**Scale/Scope**: ユーザー少数（内部開発者）・画面数 1（メイン）+ モーダル程度

## Constitution Check

| Principle | Status | 説明 |
|-----------|--------|------|
| 1. Library-First | PASS | UI用ロジックは専用モジュール (`src/lib/ui_helpers.py` 予定) で関数化しテスト可能にする |
| 2. CLI & Text Interface | PASS | 新UIは補助機能。既存APIとCLIは維持（UI導入でCLI要件は変えない） |
| 3. Test-First Enforcement | PASS | JSON検証/プリセット適用/マスキング処理に事前Failテスト追加 |
| 4. External Boundary Safety | PASS | API呼び出しは既存安全層（timeouts/retries）。UIは例外整形のみ |
| 5. Observability & Simplicity | PASS | 既存ログ活用。UI側は控えめ（送信要約を表示）。重複出現後にのみ共通化 |

=> GATE OK。Phase1後に再確認予定。

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

ios/ or android/
```text
src/
├── api/                # 既存 FastAPI
├── cli/                # 既存 CLI
├── lib/                # スクレイパ等既存ロジック + 新UI補助 (ui_helpers.py 予定)
└── ui/                 # Streamlit エントリ (app.py 予定)

tests/
├── unit/               # 既存 + 新UI補助関数テスト
└── integration/        # 必要なら簡易追加（UI除く）
```

**Structure Decision**: 単一リポジトリ内で既存 `src/` に `ui/` ディレクトリ追加し最小変更。UIロジックは `lib/` 側ヘルパでテスト可能に分離。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
