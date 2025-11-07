# Copilot Instructions for image-saver

These instructions help AI coding agents work productively in this repo. Keep responses concise and follow the repository’s conventions.

## Architecture & Intent

- Single Python project managed by uv (`pyproject.toml`). Core logic lives under `src/`.
- Main capability: scrape images from a web page and save locally; optionally upload to Google Drive using a service account.
- Public entry points:
  - Library: `src/lib/image_scraper.py` (exports `scrape_images`, `_init_drive`)
  - CLI: `python -m src.cli.scrape_images` with flags (see below)
- Tests reside under `tests/` (currently unit tests only).

## Conventions & Patterns

- CLI contracts: arguments → stdout (JSON summary), errors → stderr + non‑zero exit.
- Networking: requests with retry/backoff; parse via BeautifulSoup.
- Image detection: regex on common extensions plus fallback to path suffix check.
- File naming: SHA‑256 hash of URL + inferred extension to avoid collisions.
- Observability: use `logging` with INFO for saves/uploads and WARNING/ERROR for failures.
- Robots: robots.txt を厳密に尊重（ページ/画像 URL ともに不許可はスキップ、ページ自体が不許可なら中止）。
- Drive upload: optional dependency group `[drive]`; requires service account JSON and shared folder permissions.

## Key Files

- `src/lib/image_scraper.py`: fetch, parse, download, Drive upload helpers.
- `src/cli/scrape_images.py`: CLI argument parsing; prints a JSON summary.
- `pyproject.toml`: uv project config; install optional `[drive]` when needed.
- `README.md`: Setup (uv), usage examples, and test command.
- `.specify/memory/constitution.md`: project rules (library-first, CLI, test-first, observability, integration safety).

## Build, Run, Test (macOS/zsh)

```zsh
# Setup env
uv sync
# (Drive features)
uv pip install .[drive]

# Run scraper (output defaults to ./images)
uv run python -m src.cli.scrape_images --url https://example.com

# Tests
uv run python -m unittest discover -s tests/unit
```

## Implementation Tips (project‑specific)

- Prefer adding features as small modules under `src/` with tests first.
- When touching network/Drive boundaries, add retry and log failures; mock network in tests.
- Keep CLI non-interactive; add new flags rather than prompts.出力先はデフォルト ./images。
- Do not commit credentials; refer via env (`GDRIVE_SA_JSON`) or CLI flag.
- For new integrations, expose both library function and CLI wrapper.

## When Unsure

- Align with principles in `/.specify/memory/constitution.md`.
- If a rule must be waived, explain in PR and add minimal tests/logging.
