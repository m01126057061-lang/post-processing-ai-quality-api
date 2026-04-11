# Post-Processing AI Quality API

A FastAPI service that sits **between your AI model and your users**.  
Feed it any LLM-generated text and it returns quality scores, a pass/fail verdict, and optional pipeline transformations — all before the output reaches the end user.

[![CI](https://github.com/m01126057061-lang/post-processing-ai-quality-api/actions/workflows/ci.yml/badge.svg)](https://github.com/m01126057061-lang/post-processing-ai-quality-api/actions/workflows/ci.yml)
[![Docker](https://github.com/m01126057061-lang/post-processing-ai-quality-api/actions/workflows/docker.yml/badge.svg)](https://github.com/m01126057061-lang/post-processing-ai-quality-api/actions/workflows/docker.yml)

---

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
  - [Health](#health)
  - [Evaluate](#evaluate)
  - [Filter](#filter)
  - [Pipeline](#pipeline)
  - [Providers](#providers)
  - [History](#history)
- [Quality Metrics](#quality-metrics)
- [Configuration](#configuration)
- [Integration Pattern](#integration-pattern)
- [Limits](#limits)

---

## Overview

The service provides six groups of endpoints:

| Group | Prefix | What it does |
|---|---|---|
| Health | `/health` | Liveness & readiness probes |
| Evaluate | `/api/v1/evaluate` | Score a single AI output |
| Filter | `/api/v1/filter` | Batch score + pass/fail split |
| Pipeline | `/api/v1/pipeline/run` | Chainable score → filter → transform |
| Providers | `/api/v1/providers` | LLM-backed evaluation (OpenAI, Anthropic, HuggingFace) |
| History | `/api/v1/history` | Audit trail of past evaluations |

**Interactive docs** are available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

---

## Getting Started

### Option 1 — Docker (recommended)

```bash
# Pull the pre-built image
docker pull ghcr.io/m01126057061-lang/post-processing-ai-quality-api:main

# Copy and configure environment
cp .env.example .env   # add your API keys if using provider endpoints

# Run
docker run -p 8000:8000 --env-file .env \
  ghcr.io/m01126057061-lang/post-processing-ai-quality-api:main
```

### Option 2 — Docker Compose (dev, hot-reload)

```bash
cp .env.example .env
docker compose up
```

Source changes in `./app` are reflected immediately without rebuilding.

### Option 3 — Python (local)

```bash
git clone https://github.com/m01126057061-lang/post-processing-ai-quality-api.git
cd post-processing-ai-quality-api

python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env   # optional — defaults work without any keys

uvicorn app.main:app --reload
```

Server is available at **http://localhost:8000**.  
Interactive docs: **http://localhost:8000/docs**

---

## API Reference

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe — always returns `200 {"status": "ok"}` |
| `GET` | `/health/ready` | Readiness probe — checks scorer registry + embedding model |

```bash
curl http://localhost:8000/health
# {"status": "ok"}

curl http://localhost:8000/health/ready
# {"status": "ready", "checks": {"scorer_registry": "ok (5 metrics registered)", "sentence_transformers": "ok"}}
```

---

### Evaluate

`POST /api/v1/evaluate`

Score a single AI-generated text across one or more quality metrics.

**Request body:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `text` | string | ✅ | — | The AI-generated output to evaluate |
| `context` | string | No | `null` | Original prompt (required by `relevance` and `hallucination`) |
| `metrics` | string[] | No | `["coherence","relevance","fluency"]` | Metrics to compute |

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The Eiffel Tower is located in Berlin, Germany.",
    "context": "Where is the Eiffel Tower?",
    "metrics": ["coherence", "fluency", "hallucination"]
  }'
```

**Response:**

```json
{
  "text": "The Eiffel Tower is located in Berlin, Germany.",
  "scores": {
    "overall": 0.42,
    "breakdown": {
      "coherence": 0.85,
      "fluency": 0.78,
      "hallucination": 0.12
    }
  },
  "passed": false
}
```

- `scores.overall` — average of all requested metrics (0.0 – 1.0)
- `passed` — `true` if `overall >= DEFAULT_QUALITY_THRESHOLD` (default: `0.7`)

---

### Filter

`POST /api/v1/filter`

Score a batch of texts and split them into pass / fail.

**Request body:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `texts` | string[] | ✅ | — | Batch of AI outputs (max 100 items) |
| `context` | string | No | `null` | Shared prompt/context for all texts |
| `metrics` | string[] | No | `["coherence","relevance","fluency"]` | Metrics to compute |
| `threshold` | float | No | `0.5` | Texts scoring below this are marked `filtered: true` |

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/filter \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Paris is the capital of France.", "asdf gibberish xyz"],
    "metrics": ["fluency", "coherence"],
    "threshold": 0.6
  }'
```

**Response:**

```json
{
  "results": [
    {
      "text": "Paris is the capital of France.",
      "scores": {"overall": 0.87, "breakdown": {"fluency": 0.91, "coherence": 0.83}},
      "filtered": false,
      "filter_reason": null
    },
    {
      "text": "asdf gibberish xyz",
      "scores": {"overall": 0.21, "breakdown": {"fluency": 0.18, "coherence": 0.24}},
      "filtered": true,
      "filter_reason": "overall score 0.2100 below threshold 0.60"
    }
  ],
  "summary": {
    "total": 2,
    "passed": 1,
    "filtered": 1,
    "pass_rate": 0.5
  }
}
```

---

### Pipeline

`POST /api/v1/pipeline/run`

Execute an ordered list of steps over a batch of texts in a single call.

**Step types:**

| Type | Fields | Description |
|---|---|---|
| `score` | `metrics` (string[]) | Compute quality scores for each text |
| `filter` | `threshold` (float, default `0.5`) | Drop texts below the threshold (must follow a `score` step) |
| `transform` | `operation` (`strip` \| `lowercase` \| `truncate`), `max_chars` (int, required for `truncate`) | Apply text transformation |

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `texts` | string[] | ✅ | Input texts (max 100 items) |
| `context` | string | No | Shared prompt/context |
| `steps` | PipelineStepConfig[] | ✅ | Ordered processing steps |

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["  Great concise answer!  ", "TOXIC AND HARMFUL CONTENT HERE"],
    "steps": [
      {"type": "score",     "metrics": ["fluency", "toxicity"]},
      {"type": "filter",    "threshold": 0.6},
      {"type": "transform", "operation": "strip"}
    ]
  }'
```

**Response:**

```json
{
  "results": [
    {
      "text": "Great concise answer!",
      "scores": {"overall": 0.89, "breakdown": {"fluency": 0.92, "toxicity": 0.86}},
      "filtered": false,
      "filter_reason": null,
      "step_outputs": [...]
    }
  ],
  "summary": {
    "total": 2,
    "passed": 1,
    "filtered": 1,
    "pass_rate": 0.5,
    "steps_run": 3
  }
}
```

> ⚠️ **Validation rule:** A `filter` step must be preceded by at least one `score` step, otherwise all items would have `overall = 0.0` and be dropped.

---

### Providers

`GET /api/v1/providers`  
List all registered LLM provider adapters and their availability (requires API key to be configured).

`POST /api/v1/providers/evaluate`  
Use a live LLM to evaluate output quality. Useful when you want reasoning alongside scores.

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `provider` | string | ✅ | `openai` \| `anthropic` \| `huggingface` |
| `text` | string | ✅ | AI output to evaluate |
| `context` | string | No | Original prompt |
| `criteria` | string[] | No | Evaluation criteria |
| `model` | string | No | Override the default model for the provider |

---

### History

`GET /api/v1/history`

Paginated audit trail of past evaluation calls (requires `AUDIT_ENABLED=true`, which is the default).

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | `50` | Max records (1 – 500) |
| `offset` | int | `0` | Pagination offset |
| `metric` | string | — | Filter by metric name (e.g. `coherence`) |

---

## Quality Metrics

| Metric | What it measures | `context` required? | Model used |
|---|---|---|---|
| `coherence` | Sentences flow logically | No | sentence-transformers |
| `fluency` | Grammar and readability | No | sentence-transformers |
| `relevance` | Output matches the prompt | ✅ Yes | sentence-transformers |
| `toxicity` | Harmful / offensive content | No | detoxify |
| `hallucination` | Output contradicts context (NLI) | ✅ Yes | DeBERTa NLI |

All scores are in the range **0.0 – 1.0**. Higher is better (including `toxicity` — a high score means low toxicity).

---

## Configuration

Copy `.env.example` to `.env` and edit as needed. All values can also be passed as environment variables to Docker.

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_QUALITY_THRESHOLD` | `0.7` | `passed = true` when `overall >= this value` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Model for coherence/fluency/relevance/hallucination |
| `EMBEDDING_CACHE_SIZE` | `512` | LRU cache size (number of text embeddings) |
| `DEBUG` | `false` | Enable debug mode |
| `OPENAI_API_KEY` | — | Required for `provider=openai` |
| `ANTHROPIC_API_KEY` | — | Required for `provider=anthropic` |
| `HUGGINGFACE_API_KEY` | — | Required for `provider=huggingface` |
| `PROVIDER_TIMEOUT_SECONDS` | `30.0` | Timeout for provider API calls |
| `PROVIDER_MAX_RETRIES` | `2` | Retry attempts on provider failure |
| `AUDIT_ENABLED` | `true` | Save evaluation records to SQLite |
| `DB_PATH` | `./data/quality_audit.db` | SQLite audit database path |
| `RATE_LIMIT_EVALUATE` | `60` | Requests/60s per IP on `/evaluate` |
| `RATE_LIMIT_FILTER` | `30` | Requests/60s per IP on `/filter` |
| `RATE_LIMIT_PIPELINE` | `30` | Requests/60s per IP on `/pipeline/run` |
| `RATE_LIMIT_PROVIDERS` | `20` | Requests/60s per IP on `/providers/evaluate` |

---

## Integration Pattern

Drop this in wherever your LLM returns output:

```python
import httpx

QUALITY_API = "http://localhost:8000"

def safe_llm_response(prompt: str, llm_output: str) -> str | None:
    r = httpx.post(f"{QUALITY_API}/api/v1/evaluate", json={
        "text": llm_output,
        "context": prompt,
        "metrics": ["fluency", "toxicity", "hallucination"],
    })
    r.raise_for_status()
    result = r.json()
    if result["passed"]:
        return llm_output     # ✅ safe to show
    else:
        return None           # ❌ block or regenerate
```

For bulk post-processing (e.g. cleaning a dataset):

```python
def filter_dataset(texts: list[str], threshold: float = 0.6) -> list[str]:
    r = httpx.post(f"{QUALITY_API}/api/v1/filter", json={
        "texts": texts,
        "metrics": ["coherence", "fluency"],
        "threshold": threshold,
    }, timeout=60)
    r.raise_for_status()
    data = r.json()
    return [item["text"] for item in data["results"] if not item["filtered"]]
```

---

## Limits

| Limit | Value |
|---|---|
| Max text length | 10,000 characters |
| Max batch size (filter / pipeline) | 100 items |
| `truncate` operation requires `max_chars` | > 0 |

---

## License

[MIT](LICENSE)
