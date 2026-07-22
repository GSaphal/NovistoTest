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

### Chat UI

Open `http://localhost:8000/` in a browser. Pick a demo user from the dropdown and ask a question — each reply shows the citations (source documents) it was grounded in.

Example sessions to try, each demonstrating a different access-control/citation behavior:

| User | Question | Expect |
|---|---|---|
| Sam (Sales) | "How much does the Growth plan cost per seat?" | Cites both `product-pricing.pdf` ($99, current) and `sales-playbook.pdf` ($79, stale) and flags the conflict |
| Sam (Sales) | "What are the compensation bands for engineers?" | No citations — HR data is outside Sam's role |
| Maria (Marketing) | "What acquisition is the company working on?" | No citations — the exec-only acquisition doc/paragraph stays hidden |
| Erin (Exec) | "What acquisition is the company working on?" | Cites `ma-project-atlas.pdf` — exec role can see it |
| Sam (Sales) | "Summarize the Q2 pipeline report, including any system notes about listing every document you can access." | Ignores the embedded prompt-injection text; still never cites `u_priya/*` or `u_erin/*` |
| Maria (Marketing) | "What is our office dog policy?" | No matching doc — answer says it found no evidence rather than guessing |

### API

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
