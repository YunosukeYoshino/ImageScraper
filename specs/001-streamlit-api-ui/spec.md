# Feature Specification: APIリクエストUI

**Feature Branch**: `001-streamlit-api-ui`
**Created**: 2025-11-08
**Status**: Draft
**Input**: User description: "streamlitでapiリクエストができるUIを作成"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - 単一のAPI呼び出しを即時に試せる (Priority: P1)

ユーザーは、ベースURLを指定し、HTTPメソッド（GET/POST/PUT/DELETE など）とエンドポイントパスを入力し、必要に応じてクエリパラメータ・ヘッダー・リクエストボディ（JSON）を設定して送信できる。送信後、ステータスコード・処理時間・レスポンスボディ（JSONは整形表示、非JSONはプレーン表示）が画面に表示される。

**Why this priority**: 最小限の価値（API疎通確認・動作検証）を最短で提供でき、他の機能に依存せず単独で有用。

**Independent Test**: ベースURLを設定し、簡単なGET（例: 健康チェック用の公開エンドポイント）とJSONを伴うPOSTを個別に実行し、結果表示までが完結して価値を提供することを検証できる。

**Acceptance Scenarios**:

1. **Given** ベースURLが入力済み、**When** メソッド=GETでエンドポイントを送信、**Then** ステータスコードとレスポンス本文が表示される
2. **Given** ベースURLが入力済み・有効なJSON本文が入力済み、**When** メソッド=POSTで送信、**Then** ステータスコード・処理時間・整形済みJSONが表示される

---

### User Story 2 - 接続設定の管理（ベースURL・認証・ヘッダー） (Priority: P2)

ユーザーは、ベースURL、共通ヘッダー（例: 認可トークン等）、タイムアウトなどの接続設定を入力し、同一セッション内で再利用できる。利用者はエンドポイントごとに個別ヘッダーも追加できる。

**Why this priority**: 繰り返し利用時の入力負担を大きく下げ、実務での効率を改善するため。

**Independent Test**: 設定入力後に別のエンドポイントを実行して、設定が自動適用されていることを検証できる。

**Acceptance Scenarios**:

1. **Given** ベースURLと共通ヘッダーを保存、**When** 新しいリクエスト画面で送信、**Then** 共通ヘッダーが付与され結果が表示される
2. **Given** セッション中、**When** 画面を再読み込み、**Then** 直前の接続設定が再利用可能である（[NEEDS CLARIFICATION: セッション越えの永続化の要否と範囲（端末内保存の可否・期限）]）

---

### User Story 3 - 定型操作のプリセット実行 (Priority: P3)

ユーザーは、よく使うAPI操作をプリセットとして選択し、必要最小限の入力のみで送信できる（例: 健康チェック、特定の業務API呼び出しなど）。プリセットは名称・メソッド・パス・ひな型ボディ・期待されるレスポンス形式のメモを含む。

**Why this priority**: 繰り返し作業の短縮と入力ミスの削減に効果的で、導入ハードルを下げられるため。

**Independent Test**: プリセットを1つだけ実装しても、利用者が単独で価値を得られることをデモできる。

**Acceptance Scenarios**:

1. **Given** プリセット一覧が表示、**When** あるプリセットを選択して送信、**Then** 事前設定が反映されたリクエストが送信され、結果が表示される
2. **Given** 入力の一部を上書き、**When** 送信、**Then** 上書きがそのリクエストにのみ反映され結果が表示される

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

- JSON本文が不正（パース不能／スキーマ不整合）の場合は、送信前に入力エラーを明示する
- レスポンスが非JSON（プレーンテキスト／HTML／バイナリ）の場合は、内容に応じて安全に表示（またはダウンロード案内）する
- タイムアウトやネットワーク断などの接続失敗時は、原因分類（解決のヒント付き）を表示する
- 4xx/5xx のエラー応答は、ステータス・メッセージ・ボディを見やすく提示する
- 大きなレスポンス（サイズ/行数）の場合は、折り畳みや検索などで可読性を担保する
- APIの配置がUIとは異なるオリジンにある場合の接続要件（[NEEDS CLARIFICATION: 同一オリジン提供か、別オリジン接続前提か]）

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: ユーザーは、ベースURL・メソッド・パス・クエリ・ヘッダー・本文（JSON）を入力してリクエストを送信できる
- **FR-002**: 入力本文がJSONとして不正な場合、送信前にエラーを表示し送信を抑止する
- **FR-003**: 送信結果として、ステータスコード、処理時間、レスポンス本文（JSONは整形）を表示する
- **FR-004**: 共通の接続設定（ベースURL、共通ヘッダー、タイムアウト）をセッション内で再利用できる
- **FR-005**: エラー応答（4xx/5xx）やネットワーク失敗時の原因と対処ヒントを表示する
- **FR-006**: 非JSONレスポンスは破損なく安全に表示（またはファイルとして扱う案内）を行う
- **FR-007**: よく使う操作をプリセットとして選択し、最小入力で送信できる
- **FR-008**: リクエストとレスポンスの要約（メソッド、パス、ステータス、所要時間）を画面に記録表示できる（画面遷移で消えてよい）
- **FR-009**: 機微情報（認証トークン等）は利用者が明示入力した範囲のみで使用し、表示やログにマスクする
- **FR-010**: 接続先APIの配置前提（同一/別オリジン）の取り扱い方針を仕様化する（[NEEDS CLARIFICATION: UIとAPIの配置関係による接続要件]）

### Key Entities *(include if feature involves data)*

- **Request**: ベースURL、メソッド、パス、クエリ、ヘッダー、本文（JSONテキスト）
- **Response**: ステータスコード、処理時間、本文（JSON/テキスト/その他）、エラー情報
- **Preset**: 名称、説明、メソッド、パス、ひな型ボディ、注意事項メモ

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: 初回利用者が単純なGETリクエスト送信から結果確認までを1分以内で完了できる割合が90%以上
- **SC-002**: 正常系の有効なリクエストの95%以上で、送信から結果表示まで3秒以内に完了
- **SC-003**: 入力不備やエラー発生時、原因が特定できる表示（どの入力/どの段階か）が提供され、サポート問い合わせ率を導入前比で30%以上低減
- **SC-004**: よく使う操作（プリセット）の利用により、同操作の入力時間が従来比50%以上短縮

### Assumptions

- 対象は業務利用者（開発/運用/サポート等）であり、一般公開の不特定多数は想定しない
- 本UIはAPIの利用を補助するためのもので、長期保存や共有のためのデータ永続化は必須要件ではない（必要なら別途合意）
- 機微情報の保存・表示には配慮し、意図しない暴露を避ける

### Clarifications Needed (max 3)

1. 対象範囲: 本プロジェクトのAPIエンドポイントに限定（外部任意API送信は非対象）
2. 永続化の範囲: 接続設定（ベースURL・共通ヘッダー・タイムアウト）はローカル端末に期限なし保存（ユーザーは明示的にリセット可能）
3. 配置前提: UIとAPIは同一オリジンで提供（CORS/プロキシ要件は本バージョンで考慮不要）
