# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] — 2026-04-11

### Added

- **Prometheus `/metrics` endpoint** — `prometheus-fastapi-instrumentator` wired
  into the app; exposes standard HTTP request counts, latency histograms, and
  in-progress gauges.  Compatible with any Prometheus + Grafana setup.

- **Scorer plugin system** — drop a `.py` file in `app/scorers/plugins/` and
  any `QualityScorer` subclass is auto-discovered and registered at startup.
  No core code changes needed.  `reload_plugins()` re-scans at runtime.

- **Feedback endpoint** (`POST /api/v1/feedback`) — accepts `evaluation_id`,
  `correct (bool)`, and an optional `note`; persists to a new `feedback` table
  in the SQLite audit DB.  Lays the groundwork for future threshold recalibration
  driven by real human corrections.

- **`evaluation_id` in `/evaluate` response** — every `POST /api/v1/evaluate`
  call now persists to the audit trail and returns its record UUID.  Pass this
  ID to `/feedback` to link human corrections to specific evaluations.

- **Per-metric explanations in `/evaluate` response** — new `explanations` field
  (dict of metric → string) provides a human-readable, band-labelled description
  of each score (e.g. `"0.43 (moderate) — some logical gaps between sentences"`).
  `QualityScorer.explain()` default implementation is overridable in subclasses.

### Changed

- `POST /api/v1/evaluate` is now an `async def` endpoint (was `def`); scoring
  logic is unchanged, but the DB save is non-blocking.
- `EvaluateResponse` gains two optional fields: `evaluation_id` and `explanations`.
- `app/db/connection.py` `_SCHEMA` extended with the `feedback` table and index.
- `app/scorers/base.py` `QualityScorer` gains `explain(score)` default method
  and `requires_context` class attribute (was only on `RelevanceScorer`).

---

## [1.1.0] — 2026-04-09

### Added
- **Toxicity scorer** (`app/scorers/toxicity.py`) — multilingual BERT model via
  `detoxify`; scores 6 sub-categories (toxicity, obscene, threat, insult,
  identity_attack, severe_toxicity).
- **Hallucination scorer** (`app/scorers/hallucination.py`) — NLI cross-encoder
  (`deberta-v3-small`); returns P(entailment) as groundedness score.
- **Embedding LRU cache** — per-text `embed_one()` with configurable cache size
  (`EMBEDDING_CACHE_SIZE`, default 512). Eliminates redundant model calls in
  batch requests.
- **Rate limiting middleware** (`app/core/rate_limit.py`) — sliding window,
  IP-based; HTTP 429 + `Retry-After` on breach. Configurable per-endpoint limits.
- **SQLite audit trail** (`app/db/`) — every evaluation persisted to
  `data/quality_audit.db`. New `GET /api/v1/history` endpoint with pagination.
- **Multi-language support** — `langdetect` integration; fluency heuristics now
  adapt capitalisation rules and TTR weighting by detected language.
- **Improved fluency scorer** — 5 signals (was 4): adds Flesch Reading Ease via
  `textstat`, normalised to [0, 1].
- **Dependabot** — weekly automated dependency updates for pip and GitHub Actions.

### Changed
- `RelevanceScorer` now exposes `requires_context = True` attribute; the neutral
  `0.5` fallback is explicitly documented in docstring and OpenAPI description.

---

## [1.0.0] — 2026-04-09

### Added
- FastAPI application with `/api/v1/evaluate`, `/api/v1/filter`,
  `/api/v1/pipeline/run`, `GET /providers`, `POST /providers/evaluate`.
- Three baseline scorers: `CoherenceScorer`, `RelevanceScorer`, `FluencyScorer`.
- Pipeline engine with `ScoreStep`, `FilterStep`, `TransformStep`.
- Four model provider adapters: OpenAI, Anthropic, HuggingFace, Mock.
- Input validation: text ≤ 10 000 chars, batch ≤ 100 items.
- `RequestIDMiddleware` + structured error responses (`ErrorResponse`).
- Health endpoints: `GET /health/live`, `GET /health/ready`.
- 16-file test suite: ~85 unit + ~55 integration + 12 benchmark cases.
- Docker 2-stage build (non-root, model pre-cached, `HEALTHCHECK`).
- Three GitHub Actions workflows: CI (lint + test + audit), Docker (GHCR push),
  Release (auto-notes on `v*.*.*` tag).
- MIT License, CONTRIBUTING.md, ruff config, pyproject coverage config.
