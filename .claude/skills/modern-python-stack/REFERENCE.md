# Modern Python Stack Reference

詳細な設定テンプレートとadvanced設定。

## 目次

- [pyproject.toml完全テンプレート](#pyprojecttoml完全テンプレート)
- [Ruff詳細設定](#ruff詳細設定)
- [ty詳細設定](#ty詳細設定)
- [import-linter設定](#import-linter設定)
- [pre-commit設定](#pre-commit設定)
- [CUDA対応設定](#cuda対応設定)
- [Taskfile（オプション）](#taskfileオプション)

---

## pyproject.toml完全テンプレート

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
```

---

## Ruff詳細設定

### 推奨ルールセット

```toml
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
```

---

## ty詳細設定

### エラー抑制パターン

```python
# 単一エラー無視
result = func()  # ty: ignore[invalid-assignment]

# 複数エラー無視
value = data["key"]  # ty: ignore[possibly-unbound, invalid-assignment]

# 関数単位で無効化
from typing import no_type_check

@no_type_check
def legacy_function():
    pass
```

### 性能比較（M3 MacBook Air、1000回実行）

| ツール | 実行時間 |
|--------|----------|
| ty | 14.6秒 |
| mypy | 101秒 |

---

## import-linter設定

### Layered Architecture

```toml
[[tool.importlinter.contracts]]
name = "Layered architecture contract"
type = "layers"
layers = ["infrastructure", "adapters", "use_cases", "entities"]
```

### Clean Architecture

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

## pre-commit設定

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

## CUDA対応設定

PyTorchのCUDA版を使用する場合：

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

## Taskfile（オプション）

Makefileの代替としてTaskfile.yamlを使用する場合：

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

  check:
    desc: Run all checks
    cmds:
      - uv run ruff check .
      - uv run ty check src/
      - uv run pytest
```
