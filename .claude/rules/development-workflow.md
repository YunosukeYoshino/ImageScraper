---
description: 開発ワークフローとコード品質基準。コミット前チェック、テスト規約。
globs: ["*"]
---

# Development Workflow

## Quality Checks

コード変更後、必ず以下を実行:

```bash
# 1. フォーマット
uv run ruff format .

# 2. リント（自動修正）
uv run ruff check --fix .

# 3. テスト
uv run python -m unittest discover -s tests/unit
```

## Pre-commit Hooks

- 【MUST】`uv run pre-commit install`でフック有効化
- 【MUST】コミット前にruff check/formatが自動実行

## Git Workflow

```bash
# ブランチ作成
git checkout -b feature/xxx

# コミット（Conventional Commits推奨）
git commit -m "feat: 新機能の説明"
git commit -m "fix: バグ修正の説明"
git commit -m "refactor: リファクタリング内容"
```

## Testing Rules

- 【MUST】テストファースト: 実装前に`tests/unit/`にテスト追加
- 【MUST】モック使用: 実ネットワーク接続を避ける
- 【MUST】AAA構造: Arrange-Act-Assert

```python
def test_振る舞いを日本語で記述(self):
    # Arrange
    sut = TargetClass()

    # Act
    result = sut.method()

    # Assert
    assert result == expected
```

## Secrets

- 【MUST】サービスアカウントJSON等は絶対にコミットしない
- 【MUST】環境変数で参照（`.env`は`.gitignore`に追加）
