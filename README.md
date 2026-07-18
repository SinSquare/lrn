# lrn

Incident triage API that scores LLM outputs, reviews samples in the background, and tracks prompt improvements over time.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Poetry](https://python-poetry.org/docs/#installation) (native runs and tests)
- Python 3.13+
- A [Google Gemini](https://ai.google.dev/) API key

## Environment (`.env`)

Create a `.env` file in the project root (it is gitignored):

```bash
cat > .env <<'EOF'
LRN_GEMINI_API_KEY=your-gemini-api-key-here
EOF
```

Optional settings (defaults shown):

```bash
# Used for native runs; Docker Compose overrides this for the api service.
LRN_DB_URL=postgresql://postgres:postgres@localhost:5433/lrn_db

LRN_REVIEW_RESCORE_LIMIT=25
LRN_REVIEW_RESCORE_CONCURRENCY=5
```

All settings use the `LRN_` prefix and are loaded from `.env` via `lrn.config.Config`.

## Start with Docker

1. Create `.env` as above (at least `LRN_GEMINI_API_KEY`).
2. Build and start Postgres + API:

```bash
docker compose up -d --build
```

3. Check that the API is up:

- OpenAPI docs: http://localhost:8080/docs
- Dashboard: http://localhost:8080/dashboard

Useful commands:

```bash
# Follow API logs
docker compose logs -f api

# Stop everything
docker compose down

# Rebuild after dependency changes
docker compose build
docker compose up -d
```

Compose maps the API to host port **8080** and Postgres to host port **5433**. The API container talks to Postgres on the internal `db` hostname.

## Start natively

1. Create `.env` as above.
2. Start only the database (or point `LRN_DB_URL` at your own Postgres):

```bash
docker compose up -d db
```

3. Install dependencies and run the API:

```bash
poetry install
poetry shell
fastapi dev lrn/main.py --port 8080
```

Or without activating the shell:

```bash
poetry run fastapi dev lrn/main.py --port 8080
```

- OpenAPI docs: http://127.0.0.1:8080/docs
- Dashboard: http://127.0.0.1:8080/dashboard

Schema tables are created on startup (`SQLModel` metadata). For migration history, use Alembic from the project root:

```bash
poetry run alembic upgrade head
```

## Seed sample messages

`seed.py` posts every sample incident from `SAMPLE_MESSAGES.md` to `POST /process`. The API must already be running (Docker or native).

```bash
# Default: http://127.0.0.1:8080, 10s pause between messages
poetry run python seed.py

# Custom base URL / timing
poetry run python seed.py --base-url http://127.0.0.1:8080 --sleep 5 --timeout 120

# Or set the base URL via env
LRN_BASE_URL=http://127.0.0.1:8080 poetry run python seed.py
```

Each message is triaged, stored as a sample, and reviewed in the background (score, improvement, improved average). Seeding 25 messages takes a while because of the default sleep and LLM calls.

## Dashboard

Open http://localhost:8080/dashboard (or http://127.0.0.1:8080/dashboard when running natively).

The chart shows improved average scores over time for samples with `improvement > 0`:

1. Y-axis is `improved_average_score` (0–100)
2. Tooltips show the `improvement` percentage
3. X-axis is `created_at`

JSON series: `GET /dashboard/series`

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/process` | Triage a message and store a sample |
| `GET` | `/samples` | List samples (cursor pagination) |
| `GET` | `/prompts` | List prompts (cursor pagination) |
| `GET` | `/dashboard` | Improvement climb UI |
| `GET` | `/dashboard/series` | Chart data |

Interactive docs: `/docs`

## Development

```bash
# Tests
poetry run pytest

# Lint / format
poetry run ruff check
poetry run ruff format
```
