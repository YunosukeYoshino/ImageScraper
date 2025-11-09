<!--
Sync Impact Report
Version change: 1.0.0 -> 1.1.0
Modified principles: (added new Principle 6: Autonomous Topic Discovery & Provenance)
Added sections: Principle 6 (Autonomous Topic Discovery & Provenance)
Removed sections: None
Templates requiring updates:
	.specify/templates/plan-template.md ✅ added gating for Principle 6
	.specify/templates/spec-template.md ✅ added user story guidance for Principle 6
	.specify/templates/tasks-template.md ✅ no change needed (structure already independent)
Deferred TODOs: None
-->

# image-saver Constitution

## Core Principles

### 1. Library-First Modularity
All new functionality MUST be introduced as a small, independently testable module (library) under `src/` before any broad wiring. Each module MUST: have a single clear responsibility; expose a documented public API (functions or CLI entry point); avoid hidden global state; include at least one test validating primary behavior. Rationale: Prevents monolith bloat and enables rapid refactors.

### 2. CLI & Text Interface
User‑facing execution MUST be possible via a CLI command (`uv run python -m ...`) with arguments → stdout (results JSON or human readable) and errors → stderr + non‑zero exit code. No interactive prompts for core operations. Rationale: Enables automation, scripting, and reproducible pipelines.

### 3. Test-First Enforcement (NON-NEGOTIABLE)
For any non-trivial behavior (parsing, network logic, transformations) a failing unit or integration test MUST exist before implementation changes. Red-Green-Refactor cycle is enforced: write failing test → implement minimal pass → refactor for clarity. Rationale: Ensures correctness and documents intent.

### 4. External Boundary & Integration Safety
Network/API/file system boundaries MUST have error handling (timeouts, retries, clear exceptions). Adding or changing integration logic (e.g., Drive upload) REQUIRES: a simulated test (mock or fake) and logging of failures. Rationale: Keeps failures observable and prevents silent data loss.

### 5. Observability & Simplicity
Logging MUST use structured or at minimum leveled messages via `logging` for start/end of significant operations (fetch, download, upload). Avoid premature abstraction; refactor only after duplication appears ≥2 times. Rationale: Maintain debuggability while resisting over-engineering.

### 6. Autonomous Topic Discovery & Provenance
When the user supplies a topic/keyword (instead of a concrete URL) the system MAY autonomously discover candidate source pages. Such discovery MUST be implemented in a dedicated module (`src/lib/topic_discovery_*.py` or similar) and MUST:
- Produce a deterministic, replayable query log (inputs: topic, search queries, filters, timestamps).
- Enforce rate limiting & backoff per external search/provider (no uncontrolled bursts).
- Respect robots.txt for every discovered page before scraping images; abort page scrape if disallowed.
- Capture provenance metadata for each image: `source_page_url`, `image_url`, `discovery_method` (e.g., SERP, sitemap), and retrieval timestamp.
- Provide filtering hooks (e.g., min resolution, domain allow/deny) before download.
- Be test-covered with mocks (no live network in CI) verifying: query logging, rate limiting, provenance emission, robots exclusion handling.
Rationale: Topic-driven expansion creates compliance and reproducibility risks; strict provenance and replay logs mitigate.

## Constraints & Stack

Language: Python >=3.11.
Dependency management: uv + `pyproject.toml` (no ad-hoc requirements.txt as source of truth; requirements.txt may exist only as generated compatibility artifact). Optional extras groups for external services (e.g., `[drive]`). Network scraping MUST respect optional robots.txt flag; default is fail-open but callers can enforce `--respect-robots`.

Performance: Single-page scrape SHOULD complete <2s p95 for moderate pages (<150 images). Retry backoff MUST prevent hammering (exponential). Memory footprint SHOULD remain <100MB for standard runs.

Security: Credentials (service account JSON) MUST NOT be committed. Any future secrets handling MUST use environment variables or secret storage.

## Workflow & Quality Gates

1. Feature proposal → spec (`spec-template.md`) with independently testable user stories.
2. Plan generation (`plan-template.md`) MUST include Constitution Check referencing Principles 1–6 explicitly.
3. Tasks file groups work by user story enabling independent delivery; parallel tasks marked `[P]` MUST not share mutable files.
4. Before merge: All new tests PASS; no remaining TODOs except explicitly deferred with justification.
5. Version bumps of this constitution follow semver: MAJOR (principle redefine/removal), MINOR (new principle or section), PATCH (clarification only).

## Governance

Supremacy: This constitution supersedes informal practices. Divergence MUST be justified in PR description with a temporary waiver referencing principle number.

Amendment Procedure: Propose diff → classify bump (PATCH/MINOR/MAJOR) with rationale → obtain maintainer approval → update version line + Sync Impact Report at top.

Compliance Review: Every PR reviewer MUST verify: (a) principles not violated, (b) tests exist for behavior changes, (c) logging present for boundary operations, (d) credentials excluded.

Versioning Policy: See Workflow step 5; repository tooling MAY parse `**Version**:` line for automation.

Audit & Review Cadence: Quarterly review of principles for continued relevance; open TODOs MUST be resolved or re-justified.

**Version**: 1.1.0 | **Ratified**: 2025-11-07 | **Last Amended**: 2025-11-10
