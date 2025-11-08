# Tasks: APIリクエストUI

**Input**: plan.md, spec.md, research.md, data-model.md, contracts/
**Prerequisites**: plan.md, spec.md

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 [P] Create `src/ui/` and scaffolding for Streamlit app (`src/ui/app.py`)
- [ ] T002 [P] Add Streamlit dependency to `pyproject.toml`
- [ ] T003 Verify/augment `.gitignore` for Python/uv artifacts

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T010 [P] [US1] Add UI helper module `src/lib/ui_helpers.py` (skeleton)
- [ ] T011 [US1] Define config persistence path `~/.image-saver/ui_config.json`
- [ ] T012 [US1] Implement config load/save helpers (no UI yet)

**Checkpoint**: Helpers ready（以降のUIから利用）

---

## Phase 3: User Story 1 - 単一のAPI呼び出しを即時に試せる (P1)

### Tests (write first)
- [ ] T020 [P] [US1] tests/unit/test_ui_helpers.py: JSON検証(OK/NG)のテスト
- [ ] T021 [P] [US1] tests/unit/test_ui_helpers.py: ヘッダマスキング/URL組立のテスト

### Implementation
- [ ] T022 [US1] `src/lib/ui_helpers.py`: validate_json, mask_headers, build_full_url, summarize_response
- [ ] T023 [US1] `src/ui/app.py`: 入力フォーム（ベースURL/メソッド/パス/クエリ/ヘッダー/本文）と送信・結果表示

**Checkpoint**: US1の独立検証（GET/POSTで結果表示まで）

---

## Phase 4: User Story 2 - 接続設定の管理 (P2)

### Tests
- [ ] T030 [US2] tests/unit/test_ui_helpers.py: Config load/save（上書き/マスキング）

### Implementation
- [ ] T031 [US2] `src/lib/ui_helpers.py`: config load/save 実装（期限なしローカル保存）
- [ ] T032 [US2] `src/ui/app.py`: 共通ヘッダー/タイムアウトの保存と自動適用

**Checkpoint**: 設定がセッション越えで再利用可（ローカル保存）

---

## Phase 5: User Story 3 - プリセット実行 (P3)

### Tests
- [ ] T040 [US3] tests/unit/test_ui_helpers.py: プリセット適用の単体テスト

### Implementation
- [ ] T041 [US3] `src/lib/ui_helpers.py`: プリセット構造と適用関数
- [ ] T042 [US3] `src/ui/app.py`: プリセット選択UI + 上書き適用送信

**Checkpoint**: プリセット1件で動作デモ可

---

## Phase N: Polish

- [ ] T090 [P] README/quickstart更新
- [ ] T091 ロギング/ユーザー向けメッセージ微調整
- [ ] T092 画面の折り畳み/検索/コピー操作の改善（最小限）

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 → US2 → US3 → Polish
- [P] は並行可能、同一ファイルを触るものは順次実行
- 各ストーリー完了毎にチェックポイントで独立検証
