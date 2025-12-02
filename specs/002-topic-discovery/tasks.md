---

description: "Task list for 002-topic-discovery"
---

# Tasks: 002-topic-discovery

**Input**: Design documents from `/specs/002-topic-discovery/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are OPTIONAL in this list; however implementation tasks include unit tests inline to comply with the Constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add base modules and folders required by topic discovery

- [X] T001 Create discovery logs folder `discovery_logs/` at repo root
- [X] T002 [P] Add `src/lib/models_discovery.py` with `ProvenanceEntry` (pydantic) and `QueryLogEntry`
- [X] T003 [P] Add `src/lib/rate_limit.py` simple token bucket (configurable RPS)
- [X] T004 Add `src/lib/topic_discovery.py` orchestrator skeleton (no network yet)
- [X] T005 Update `README.md` with new `--topic/--topics` usage (placeholder section)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement boundary safety and schema needed by all stories

- [X] T006 Implement robots.txt check helper in `src/lib/image_scraper.py` (reusable) and export
- [X] T007 [P] Implement rate limiting in `src/lib/rate_limit.py` with unit tests in `tests/unit/test_rate_limit.py`
- [X] T008 [P] Implement provenance/query log models with validation and unit tests in `tests/unit/test_provenance_models.py`
- [X] T009 Wire logging for discovery lifecycle in `src/lib/topic_discovery.py` (INFO/WARN)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Single Topic Preview (Priority: P1) 🎯 MVP

**Goal**: Accept a topic keyword and produce preview JSON with provenance entries (no download)

**Independent Test**: Using mocked provider HTML/JSON, ensure deterministic query log file is written and provenance has required fields; robots-disallowed pages are skipped.

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `discover_topic(topic: str, limit: int=50)` in `src/lib/topic_discovery.py`
- [X] T011 [P] [US1] Add provider adapter `search_provider.py` in `src/lib/` (duckduckgo/html-serp fallback)
- [X] T012 [US1] Integrate robots check before page scrape in `src/lib/topic_discovery.py`
- [X] T013 [US1] Write deterministic query log per topic to `discovery_logs/{YYYYMMDD}_{topic}.json`
- [X] T014 [US1] Extend CLI `src/cli/scrape_images.py` to accept `--topic` and output preview JSON to stdout
- [X] T015 [US1] Update Streamlit `src/ui/image_scraper_app.py` to add Topic input and preview listing
- [X] T016 [US1] Add unit tests in `tests/unit/test_topic_discovery.py` for: query log writing, provenance shape, robots skip

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Selective Download With Filters (Priority: P2)

**Goal**: Apply filters and download selected images; save provenance sidecar index

**Independent Test**: Provide selected entries with mocks; verify downloaded files and `provenance_index.json` saved.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Add filters (min width/height, domain allow/deny) in `src/lib/topic_discovery.py`
- [ ] T018 [US2] Extend `src/lib/image_scraper.py` download path to accept provenance and write `provenance_index.json` to output dir
- [ ] T019 [US2] Extend CLI `src/cli/scrape_images.py` with `--min-resolution`, `--allow-domain`, `--deny-domain`
- [ ] T020 [US2] Update Streamlit `src/ui/image_scraper_app.py` to support filtering + selection and trigger download
- [ ] T021 [US2] Add unit tests in `tests/unit/test_topic_discovery.py` for filters and provenance index writing

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Multi-Topic Batch & Dedup (Priority: P3)

**Goal**: Handle multiple topics with batch discovery, rate limiting, and deduplication

**Independent Test**: Mock overlapping topics; assert deduped entries and rate limit behavior (timed tokens consumption)

### Implementation for User Story 3

- [ ] T022 [P] [US3] Accept `--topics"a,b,c"` in `src/cli/scrape_images.py` and batch in `src/lib/topic_discovery.py`
- [ ] T023 [US3] Implement dedup by `image_url` across topics in `src/lib/topic_discovery.py`
- [ ] T024 [US3] Merge provenance across topics and emit combined index
- [ ] T025 [US3] Update Streamlit `src/ui/image_scraper_app.py` to support multiple topics input
- [ ] T026 [US3] Add unit tests in `tests/unit/test_topic_discovery.py` for batch + dedup + rate limiting

**Checkpoint**: All user stories independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

- [ ] T027 [P] Documentation updates in `README.md` (CLI/UI examples for topics)
- [ ] T028 Code cleanup and refactor providers into strategy pattern in `src/lib/search_providers/`
- [ ] T029 Performance optimizations: cache robots results in-memory (TTL)
- [ ] T030 [P] Additional unit tests in `tests/unit/` for error scenarios
- [ ] T031 Security hardening: sanitize topic input, path handling
- [ ] T032 Validate `quickstart.md` instructions for topic flows

---

## Dependencies & Execution Order

### Phase Dependencies
- Setup (Phase 1): No dependencies - can start immediately
- Foundational (Phase 2): Depends on Setup completion - BLOCKS all user stories
- User Stories (Phase 3+): All depend on Foundational phase completion; proceed P1→P2→P3 by priority or in parallel where capacity allows
- Polish: Depends on desired user stories completion

### User Story Dependencies
- User Story 1 (P1): Can start after Foundational; no dependency on other stories
- User Story 2 (P2): Depends on US1 preview data shape and selection integration
- User Story 3 (P3): Depends on US1 core discovery

### Within Each User Story
- Models before orchestrator
- Orchestrator before CLI/UI integration
- Filters/dedup after preview path stable

### Parallel Opportunities
- [P] marked tasks across different files: models, rate limit helper, CLI/UI changes can proceed in parallel after foundation

---

## Parallel Example: User Story 1

```
Task: "Implement discover_topic in src/lib/topic_discovery.py"
Task: "Add provider adapter in src/lib/search_provider.py"
Task: "Extend CLI with --topic in src/cli/scrape_images.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Setup + Foundational
2. Implement US1 discovery + CLI + UI preview
3. Validate preview JSON and logs
4. Demo/ship

### Incremental Delivery
1. US1 → testable MVP
2. US2 → selective download + provenance index
3. US3 → multi-topic and dedup
