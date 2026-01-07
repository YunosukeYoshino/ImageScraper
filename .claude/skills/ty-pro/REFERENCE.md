# ty Rules Reference

tyの主要ルール一覧。全ルールは[公式ドキュメント](https://docs.astral.sh/ty/reference/rules/)を参照。

## 目次

- [呼び出し・引数](#呼び出し引数)
- [割り当て・型](#割り当て型)
- [属性・アクセス](#属性アクセス)
- [インポート・参照](#インポート参照)
- [クラス・継承](#クラス継承)
- [オーバーロード・オーバーライド](#オーバーロードオーバーライド)
- [サプレッション衛生](#サプレッション衛生)
- [その他](#その他)

---

## 呼び出し・引数

| ルール | 説明 |
|--------|------|
| `call-non-callable` | 非呼び出し可能オブジェクトの呼び出し |
| `invalid-argument-type` | 無効な引数型 |
| `missing-argument` | 必須引数の欠落 |
| `too-many-positional-arguments` | 位置引数が多すぎる |
| `unknown-argument` | 不明な引数名 |
| `no-matching-overload` | マッチするオーバーロードなし |

---

## 割り当て・型

| ルール | 説明 |
|--------|------|
| `invalid-assignment` | 無効な代入 |
| `invalid-declaration` | 無効な宣言 |
| `invalid-return-type` | 戻り値型の不一致 |
| `invalid-parameter-default` | デフォルト値の型不一致 |
| `conflicting-declarations` | 競合する宣言 |

---

## 属性・アクセス

| ルール | 説明 |
|--------|------|
| `invalid-attribute-access` | 無効な属性アクセス |
| `unresolved-attribute` | 未解決の属性 |
| `possibly-missing-attribute` | 属性が存在しない可能性 |
| `not-subscriptable` | サブスクリプト不可 |
| `not-iterable` | イテレーション不可 |
| `invalid-key` | 無効なキー |
| `index-out-of-bounds` | 境界外インデックス |

---

## インポート・参照

| ルール | 説明 |
|--------|------|
| `unresolved-import` | 未解決のインポート |
| `unresolved-reference` | 未解決の参照 |
| `possibly-unresolved-reference` | 未解決の可能性 |
| `unresolved-global` | 未解決のグローバル |

---

## クラス・継承

| ルール | 説明 |
|--------|------|
| `invalid-base` | 無効な基底クラス |
| `duplicate-base` | 重複した基底クラス |
| `inconsistent-mro` | MRO不整合 |
| `subclass-of-final-class` | finalクラスの継承 |
| `invalid-metaclass` | 無効なメタクラス |

---

## オーバーロード・オーバーライド

| ルール | 説明 |
|--------|------|
| `invalid-overload` | 無効なオーバーロード |
| `invalid-method-override` | 無効なメソッドオーバーライド |
| `override-of-final-method` | finalメソッドのオーバーライド |

---

## サプレッション衛生

| ルール | 説明 | 推奨設定 |
|--------|------|----------|
| `unused-ignore-comment` | 不要なignoreコメント | `error` |
| `ignore-comment-unknown-rule` | 無効なルール名 | `error` |
| `invalid-ignore-comment` | 無効なignore構文 | `error` |

**推奨設定**:
```toml
[tool.ty.rules]
unused-ignore-comment = "error"
ignore-comment-unknown-rule = "error"
```

---

## その他

| ルール | 説明 |
|--------|------|
| `unsupported-operator` | 未サポート演算子 |
| `division-by-zero` | ゼロ除算 |
| `invalid-context-manager` | 無効なコンテキストマネージャ |
| `invalid-await` | 無効なawait |
| `invalid-raise` | 無効なraise |
| `deprecated` | 非推奨の使用 |
| `redundant-cast` | 冗長なcast |

---

## ルールレベル

各ルールは3つのレベルで設定可能:

| レベル | 動作 |
|--------|------|
| `error` | エラー報告、終了コード1 |
| `warn` | 警告報告、終了コード0 |
| `ignore` | 無効化 |

```bash
# コマンドライン
ty check --error invalid-assignment --warn index-out-of-bounds

# pyproject.toml
[tool.ty.rules]
invalid-assignment = "error"
index-out-of-bounds = "warn"
```
