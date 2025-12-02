# Feature Specification: 002-topic-discovery

**Feature Branch**: `002-topic-discovery`
**Created**: 2025-11-10
**Status**: Draft
**Input**: User description: "ユーザーが興味のあるトピック（検索ワード）を入力すると自律的に調べて画像を保存"

## User Scenarios & Testing *(mandatory)*

> Advisory for topic-based discovery features (Principle 6): Include at least one story that starts from a user-provided topic/keyword and validates: (a) deterministic query logging, (b) robots.txt respect for discovered pages, and (c) provenance fields present for every saved image.

### User Story 1 - Single Topic Preview (Priority: P1)
User enters a topic keyword. System queries provider, builds candidate page list, extracts image URLs (metadata only, no download) and returns preview + counts.

**Why this priority**: Establish core discovery and provenance data path.

**Independent Test**: Provide mock search HTML; assert query log written; assert preview JSON contains provenance fields and robots-disallowed pages skipped.

**Acceptance Scenarios**:
1. Given topic "富士山", When discovery runs, Then preview JSON lists ≥1 images with provenance fields.
2. Given a page disallowed by robots, When encountered, Then image entries from that page absent and log contains skip reason.

---

### User Story 2 - Selective Download With Filters (Priority: P2)
User selects subset of preview images applying filters (min resolution, domain whitelist) and triggers download; saved files include provenance index sidecar.

**Why this priority**: Enables practical selective saving with traceability.

**Independent Test**: Mock image URLs; simulate selection; assert downloaded filenames + provenance index file; filter excludes small images.

**Acceptance Scenarios**:
1. Given selected 5 images and min resolution filter, When download executes, Then only qualifying images saved and provenance index contains 5 entries.
2. Given domain blacklist, When download executes, Then blacklisted domain images excluded.

---

### User Story 3 - Multi-Topic Batch & Dedup (Priority: P3)
User enters multiple topics; system batches discovery with rate limiting and deduplicates identical image URLs returning merged provenance index.

**Why this priority**: Improves efficiency and user workflow across related topics.

**Independent Test**: Provide two topics producing overlapping mock URLs; assert rate limiting honored (timing tokens), final provenance index deduped.

**Acceptance Scenarios**:
1. Given topics A and B with overlap, When batch discovery runs, Then merged index has no duplicate image_url entries.
2. Given rapid successive queries, When rate limit exceeded, Then system delays requests (logged) without error.

### Edge Cases
- Empty topic keyword
- Provider returns zero results
- Timeout fetching SERP
- Robots file unreachable (treat as allow?)
- Duplicate images across pages/domains

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST accept `--topic` (single keyword) and produce preview JSON with provenance.
- **FR-002**: System MUST write deterministic query log file per topic in `./discovery_logs`.
- **FR-003**: System MUST respect robots.txt for every candidate page before extraction.
- **FR-004**: System MUST attach provenance (`source_page_url`, `image_url`, `discovery_method`, timestamp) to each image entry.
- **FR-005**: System MUST filter images by resolution and domain allow/deny lists before download.
- **FR-006 (Topic Discovery)**: When a topic/keyword is provided, the system MUST record a deterministic query log, apply rate limiting, respect robots.txt for discovered pages, and attach provenance (`source_page_url`, `image_url`, `discovery_method`, timestamp) to each saved image.
- **FR-007**: System MUST support multiple topics via comma-separated `--topics` and deduplicate image URLs.

*Example of marking unclear requirements:*
- **FR-008**: System MUST support configurable search provider [NEEDS CLARIFICATION: provider list]

### Key Entities
- **ProvenanceEntry**: source_page_url, image_url, discovery_method, timestamp, topic
- **QueryLogEntry**: topic, provider, query, timestamp, page_count, image_count

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: Preview for a single topic completes <3s p95
- **SC-002**: Robots-disallowed pages never appear in provenance index
- **SC-003**: Multi-topic dedup reduces total entries by ≥10% when overlap exists
- **SC-004**: Query log replay reproduces identical preview set for same topic within 24h (assuming provider stability)
