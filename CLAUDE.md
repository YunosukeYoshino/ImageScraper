# CLAUDE.md

Claude Code (claude.ai/code) 向けのプロジェクトガイダンス。

## Overview

**image-saver** - Webページから画像をスクレイピングしてローカル保存、オプションでGoogle Driveへアップロード。トピック探索機能（プロベナンス記録付き）も搭載。

| 項目 | 値 |
|------|-----|
| 言語 | Python 3.11+ |
| パッケージ管理 | uv（`pyproject.toml`） |
| アーキテクチャ | Clean Architecture |

## Commands

**`make help` で全コマンド一覧表示**

```bash
make setup    # 初回セットアップ
make ui       # Streamlit UI起動
make api      # FastAPI起動
make test     # テスト実行
make check    # フォーマット + リント + テスト
```

CLI: `uv run image-scrape --help`

## Rules

ルールは `.claude/rules/` に配置され、ファイルパスに基づいて自動適用される。

| ルール | 適用範囲 | 内容 |
|--------|----------|------|
| `uv-usage.md` | `*` | uvパッケージ管理の規約 |
| `python-patterns.md` | `*.py` | 型ヒント、import順序、エラーハンドリング |
| `development-workflow.md` | `*` | **コマンド一覧**、品質チェック、Git、テスト規約 |

## Skills

スキルは `.claude/skills/` に配置され、Claudeが自動的に判断して使用する。

| スキル | 説明 | 適用場面 |
|--------|------|----------|
| `modern-python-stack` | uv, Ruff, tyによるモダンPython開発 | プロジェクト作成、依存管理、品質改善 |
| `ty-pro` | Python型安全性の強化 | 型アノテーション追加、型エラー修正 |
| `tdd` | t.wada流TDD | 新機能実装、バグ修正、リファクタリング |

## Architecture

```
src/
├── lib/           # コアロジック（詳細: src/lib/README.md）
│   ├── domain/        # エンティティ、ビジネスロジック
│   ├── application/   # ユースケース
│   └── infrastructure/# HTTP、パーサー、ストレージ
├── api/           # FastAPI
├── ui/            # Streamlit UI（詳細: src/ui/README.md）
└── cli/           # CLIエントリポイント
tests/unit/        # ユニットテスト（モック使用）
```

**依存方向**: domain ← application ← infrastructure

## Key Patterns

- **CLI Contract**: 引数→stdout（JSON）、エラー→stderr + 非ゼロ終了
- **robots.txt**: ページ・画像両方で厳密に尊重
- **ファイル命名**: URLのSHA-256ハッシュ + 拡張子
- **テストファースト**: 実装前に`tests/unit/`にテスト追加

## References

- OpenAPI: http://localhost:8000/docs
