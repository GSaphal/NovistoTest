# Internal Knowledge Assistant

## Prerequisites

- Docker + Docker Compose
- Python 3.12

## Setup

1. Copy the env template and fill in your OpenAI key:
   ```bash
   cp .env.example .env
   ```

2. Start the stack (Postgres + pgvector, the MCP server, and the agent API):
   ```bash
   docker compose up -d --build
   ```

3. Ingest the sample document corpus into the database:
   ```bash
   docker compose --profile tools run --rm ingest
   ```

The API is now available at `http://localhost:8000`.

## Using it

```bash
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer tok_sales_demo" \
  -H "Content-Type: application/json" \
  -d '{"question": "How much does the Growth plan cost?"}'
```

See `data/users.json` for the other demo tokens/roles.

## Running tests locally

Create a venv and install dependencies:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

Then run:
```bash
.venv/bin/pytest -m unit          # no external dependencies
.venv/bin/pytest -m integration   # requires the db container (docker compose up -d db)
.venv/bin/pytest -m e2e           # requires the full stack up and ingested (see Setup)
```

`.env` is loaded automatically by pytest. For `integration`/`e2e` tests run from the host, `DATABASE_URL` in `.env` must point at `localhost` rather than the `db` service hostname.

## Stopping

```bash
docker compose down
```
