---
name: modern-python-stack
description: Astral社製ツール（uv, Ruff, ty）を中心としたモダンPython開発環境。新規プロジェクト作成、依存関係管理、コード品質改善、CI/CD設定時に自動適用。高速・堅牢な開発ワークフローを実現。
---

# Modern Python Stack Rules

Astral社製ツールを中心とした高速・堅牢なPython開発環境ガイドライン。

## 技術スタック概要

| カテゴリ | ツール | 特徴 |
|---------|--------|------|
| パッケージ管理 | **uv** | Rust製、pip比10-100倍高速 |
| リンター/フォーマッター | **Ruff** | Rust製、極めて高速、設定一元管理 |
| 型チェッカー | **ty** | Astral社製、mypy比大幅高速化 |
| 依存性制御 | **import-linter** | アーキテクチャ境界の強制 |
| タスク自動化 | **Taskfile** | YAMLベース、可読性重視 |
| コミット前チェック | **pre-commit** | 自動品質担保 |

## 適用場面

- 新規Pythonプロジェクトのセットアップ時
- 依存関係の追加・管理時
- コード品質改善の提案時
- CI/CD設定の構築時
- リファクタリング時

---

## 1. パッケージ管理: uv

### 原則
- 【MUST】`uv`をパッケージ管理に使用
- 【MUST】`pyproject.toml`で依存関係を一元管理
- 【SHOULD】`uv.lock`をgitにコミット（再現性確保）

### コマンド
```bash
# 環境セットアップ
uv sync

# パッケージ追加
uv add requests
uv add --dev pytest

# スクリプト実行
uv run python script.py
uv run pytest
```

### CUDA対応設定
```toml
[project]
dependencies = ["torch==2.1.2"]

[tool.uv.sources]
torch = [{ index = "pytorch-cuda", marker = "platform_system == 'Linux'" }]

[[tool.uv.index]]
name = "pytorch-cuda"
url = "https://download.pytorch.org/whl/cu121"
explicit = true
```

---

## 2. リンター/フォーマッター: Ruff

### 原則
- 【MUST】行長は`120`文字
- 【MUST】importは`force-single-line = true`（マージコンフリクト防止）
- 【SHOULD】`pyproject.toml`で設定を一元管理

### 推奨設定
```toml
[tool.ruff]
line-length = 120
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.ruff.lint]
select = [
    "A",    # flake8-builtins
    "B",    # flake8-bugbear
    "E",    # pycodestyle errors
    "F",    # Pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "W",    # pycodestyle warnings
    "PL",   # Pylint
    "UP",   # pyupgrade
]
ignore = [
    "B905",     # zip-without-explicit-strict
    "F403",     # star-imports
    "N812",     # lowercase-imported-as-non-lowercase
    "N999",     # invalid-module-name
    "PLR0912",  # too-many-branches
    "PLR0913",  # too-many-arguments
]

[tool.ruff.lint.isort]
force-single-line = true
known-first-party = ["src"]
```

### コマンド
```bash
uv run ruff check .          # リント
uv run ruff check --fix .    # 自動修正
uv run ruff format .         # フォーマット
```

---

## 3. 型チェッカー: ty

### 原則
- 【SHOULD】`ty`を型チェックに使用（mypy比で大幅高速化）
- 【MAY】段階的に型アノテーションを追加

### セットアップ
```bash
uv add --dev ty
uv run ty check src/
```

---

## 4. 依存性制御: import-linter

### 原則
- 【SHOULD】レイヤードアーキテクチャの境界をコードで強制
- 【MUST】依存方向: `infrastructure → adapters → use_cases → entities`

### 設定例
```toml
[tool.importlinter]
root_packages = ["src"]

[[tool.importlinter.contracts]]
name = "Layered architecture contract"
type = "layers"
layers = ["infrastructure", "adapters", "use_cases", "entities"]
```

### Clean Architectureの場合
```toml
[[tool.importlinter.contracts]]
name = "Clean Architecture contract"
type = "layers"
layers = ["infrastructure", "application", "domain"]
```

### コマンド
```bash
uv run lint-imports
```

---

## 5. タスク自動化: Taskfile

### 原則
- 【SHOULD】`Taskfile.yaml`でタスクを定義（Makefileより可読性向上）
- 【MUST】各タスクに`desc`で説明を付与

### Taskfile.yaml テンプレート
```yaml
version: '3'

tasks:
  default:
    desc: Show available tasks
    cmds:
      - task --list

  setup:
    desc: Setup development environment
    cmds:
      - uv sync
      - uv run pre-commit install

  lint:
    desc: Run linter
    cmds:
      - uv run ruff check .

  format:
    desc: Format code
    cmds:
      - uv run ruff format .

  type-check:
    desc: Run type checker
    cmds:
      - uv run ty check src/

  test:
    desc: Run tests
    cmds:
      - uv run pytest

  check:
    desc: Run all checks
    cmds:
      - task: lint
      - task: type-check
      - task: test
```

---

## 6. コミット前チェック: pre-commit

### 原則
- 【MUST】`pre-commit`をセットアップ
- 【MUST】Ruffをフック登録

### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: import-linter
        name: import-linter
        entry: uv run lint-imports
        language: system
        pass_filenames: false
        types: [python]
```

---

## pyproject.toml テンプレート

```toml
[project]
name = "your-project"
version = "0.1.0"
description = "Your project description"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pre-commit>=3.7.0",
    "ruff>=0.9.0",
    "ty>=0.0.1a0",
    "import-linter>=2.0.0",
    "pytest>=8.0.0",
]

[tool.ruff]
line-length = 120
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.ruff.lint]
select = ["A", "B", "E", "F", "I", "N", "W", "PL", "UP"]
ignore = ["B905", "F403", "N812", "N999", "PLR0912", "PLR0913"]

[tool.ruff.lint.isort]
force-single-line = true
known-first-party = ["src"]

[tool.importlinter]
root_packages = ["src"]

[[tool.importlinter.contracts]]
name = "Clean Architecture contract"
type = "layers"
layers = ["infrastructure", "application", "domain"]

[tool.uv]
# Minimal uv configuration
```

---

## Checklist

プロジェクトセットアップ時の確認項目:

- [ ] uvがインストールされている
- [ ] pyproject.tomlにRuff設定がある
- [ ] pre-commit hookが有効化されている
- [ ] import-linter契約が定義されている（アーキテクチャ強制時）
- [ ] Taskfile.yamlがある（タスク自動化時）
- [ ] CIでruff check/format/tyが実行される

## References

- [uv Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [ty (Astral)](https://github.com/astral-sh/ty)
- [import-linter](https://import-linter.readthedocs.io/)
- [Taskfile](https://taskfile.dev/)
- [pre-commit](https://pre-commit.com/)
