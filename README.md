# ContractOps

Contract obligation, renewal and deadline workspace.
Users: Analyst, Approver, Admin.

Stack: FastAPI + PostgreSQL (pgvector) + SQLAlchemy + Alembic + Docker Compose.
Frontend (React) comes later — see `frontend/` placeholder.

## Day 1 — skeleton only

```
contractops/
  docker-compose.yml   # db (pgvector) + api
  .env.example         # copy to .env locally, never commit .env
  backend/
    Dockerfile
    requirements.txt
    app/main.py        # GET /health only
  frontend/            # React later
```

## Run (Day 1)

1. Copy env: `Copy-Item .env.example .env`
2. Start db + api: `docker compose up --build`
3. Check: `http://localhost:8000/health` → `{"status":"ok"}`
4. Stop: `docker compose down`

Note: inside Docker the backend uses host `db` (service name), not `localhost`.
See `DATABASE_URL` in `.env.example`.

## Rules

- Small steps, one file explained at a time.
- Never commit secrets: `.env` is gitignored, only `.env.example` is committed.
