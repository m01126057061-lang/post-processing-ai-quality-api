# Contributing

## Local development setup

```bash
# 1. Clone
git clone https://github.com/m01126057061-lang/post-processing-ai-quality-api
cd post-processing-ai-quality-api

# 2. Virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env template
cp .env.example .env
# edit .env and fill in your API keys

# 5. Run the API locally
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

## Docker

```bash
# Build
docker build -t quality-api .

# Run
docker compose up

# With production overrides
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Running tests

```bash
make test            # all tests
make test-unit       # unit only (fast, no ML models loaded)
make test-integration
make coverage        # with HTML report → htmlcov/index.html
make bench           # performance benchmarks
```

## CI/CD

| Workflow | Trigger | Actions |
|----------|---------|---------|
| `ci.yml` | push / PR → main | lint (ruff), unit tests, integration tests, pip-audit |
| `docker.yml` | push → main, `v*.*.*` tag | build + push to GHCR |
| `release.yml` | `v*.*.*` tag | create GitHub Release with auto-notes |

## Releasing a new version

```bash
git tag v0.2.0
git push origin v0.2.0
```

This triggers `docker.yml` (builds `ghcr.io/.../post-processing-ai-quality-api:0.2.0`) and
`release.yml` (creates a GitHub Release with auto-generated notes).
