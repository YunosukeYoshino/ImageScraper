---
description: uvパッケージマネージャの使用規約。依存関係管理、スクリプト実行時に適用。
globs: ["*"]
---

# uv Usage Rules

## Package Manager

- 【MUST】パッケージ管理には`uv`を使用（pip/poetry/pipenv禁止）
- 【MUST】依存関係は`pyproject.toml`で一元管理
- 【SHOULD】`uv.lock`をgitにコミット（再現性確保）

## Commands

```bash
# 環境セットアップ
uv sync

# パッケージ追加
uv add <package>
uv add --dev <package>  # 開発依存

# スクリプト実行（常にuv run経由）
uv run python script.py
uv run pytest
uv run ruff check .
```

## Prohibited

```bash
# ❌ 禁止
pip install <package>
python script.py  # 直接実行

# ✅ 正しい
uv add <package>
uv run python script.py
```
