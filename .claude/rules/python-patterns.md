---
description: Pythonコードパターンと型安全性ルール。Ruff/ty設定に準拠。
globs: ["**/*.py"]
---

# Python Code Patterns

## Ruff Configuration

- 【MUST】行長は`120`文字以内
- 【MUST】importは1行1つ（`force-single-line = true`）
- 【MUST】フォーマット: `uv run ruff format .`
- 【MUST】リント: `uv run ruff check --fix .`

## Type Hints

```python
# ✅ Good: 型アノテーション付き
def fetch_images(url: str, limit: int = 10) -> list[ImageInfo]:
    ...

# ❌ Bad: 型なし
def fetch_images(url, limit=10):
    ...
```

## Import Order (isort)

```python
# 1. 標準ライブラリ
import os
from pathlib import Path

# 2. サードパーティ
import httpx
from fastapi import FastAPI

# 3. ローカル（src）
from src.lib.domain.entities import ImageInfo
```

## Error Handling

```python
# ✅ Good: 具体的な例外
try:
    response = httpx.get(url)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error: {e.response.status_code}")
    raise

# ❌ Bad: 裸のexcept
try:
    ...
except:
    pass
```

## Clean Architecture Compliance

```
依存方向: domain ← application ← infrastructure
         (内側)                    (外側)

- domain/: 外部依存なし（純粋Python）
- application/: domainのみimport可
- infrastructure/: 全層import可
```
