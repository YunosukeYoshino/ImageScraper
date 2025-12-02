# Implementation Plan: 002-topic-discovery

**Branch**: `002-topic-discovery` | **Date**: 2025-11-10 | **Spec**: ./spec.md
**Input**: Feature specification from `/specs/002-topic-discovery/spec.md`

## Summary

Add autonomous topic keyword based image source discovery: user supplies topic (e.g., "富士山 紅葉") and system discovers candidate pages, extracts image URLs with provenance, letting user preview and selectively download.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: requests, BeautifulSoup, (optional) duckduckgo_search (fallback to simple Bing/Google HTML SERP parsing if excluded)
**Storage**: local filesystem (`./images` + new `./discovery_logs`)
**Testing**: unittest + mocks (no live network)
**Target Platform**: macOS/Linux CLI + Streamlit UI
**Project Type**: single
**Performance Goals**: <3s to produce first 20 candidate images for typical topic
**Constraints**: Respect robots; maximum 2 RPS to any search provider; memory <150MB
**Scale/Scope**: Initial P1 single search provider (DuckDuckGo or HTML fallback), later P2 multi-provider, P3 filtering enhancements

## Constitution Check

Verify alignment with image-saver Constitution:
- P1 Library-First: New code under `src/lib/topic_discovery.py` + helpers, tests present.
- P2 CLI & Text: New CLI flag `--topic` enabling discovery path; stdout JSON summary.
- P3 Test-First: Failing tests for query logging, provenance schema, robots skip before impl.
- P4 Boundary Safety: Retry + timeout + rate limiting (token bucket) for search fetch.
- P5 Observability: INFO logs for discover start/end, per provider, counts; WARNING on robots skip.
- P6 Autonomous Topic Discovery: Deterministic log file & in-memory structure; provenance fields for each image; mocks in tests.

## Project Structure

### Documentation (this feature)

```text
aSpecs/002-topic-discovery/
├── plan.md
├── research.md (optional)
├── data-model.md
├── quickstart.md
├── contracts/
└── spec.md
```

### Source Code additions

```text
src/
├── lib/
│   ├── topic_discovery.py        # orchestrator
│   ├── rate_limit.py             # simple token bucket (new)
│   └── models_discovery.py       # pydantic models for provenance
├── cli/
│   └── scrape_images.py          # extended arg parsing for --topic
└── ui/
    └── image_scraper_app.py      # integrate topic input + preview

tests/unit/
├── test_topic_discovery.py
├── test_rate_limit.py
└── test_provenance_models.py
```

**Structure Decision**: Single project; new modules colocated in existing `src/lib/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (none) | - | - |
