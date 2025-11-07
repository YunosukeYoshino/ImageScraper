# Research (Phase 0)

## Decision: FastAPI でAPI層を追加（同期実装で十分）
- Rationale: 既存の同期I/Oロジックを活かし、最小コストでHTTP化できる。FastAPIは型/スキーマ連携とOpenAPI自動生成が強力。
- Alternatives considered:
  - Flask: シンプルだが型支援/スキーマの自動化が弱い。
  - Starlette直: 柔軟だがルーティング/バリデーションを自前実装する負担が大きい。
  - aiohttp: フル非同期だが既存同期関数の書き換えが発生。

## Decision: 依存は `fastapi`, `uvicorn[standard]` のみ追加
- Rationale: pydanticはFastAPI依存に含まれる。最小依存で導入する。
- Alternatives considered: gunicorn+uvicorn workers -> 後続のデプロイ段階で検討。

## Decision: API契約（入出力）
- Rationale: CLIのJSONサマリーと整合性を重視。以下のRequest/Responseを定義。
- Request: { url: str, output_dir?: str, respect_robots?: bool, upload_to_drive?: bool, drive_folder_id?: str }
- Response: { saved: int, failed: int, output_dir: str, uploaded?: int, warnings?: [str], errors?: [str], files?: [str] }
- Alternatives considered: 非同期ジョブ化（キューイング）は将来の拡張。

## Decision: エラー設計
- Rationale: ライブラリの例外をHTTPへマッピング。
  - robots不許可: 403
  - バリデーション: 400
  - 予期しない失敗: 500
- Alternatives considered: 全て200でエラーをボディに含める → API慣習に反するため不採用。

## Decision: テスト方針
- Rationale: 憲法のTest-Firstを満たす。APIユニットテストを先に追加。
- Alternatives considered: E2Eのみ → 境界条件が手薄になるため不採用。
