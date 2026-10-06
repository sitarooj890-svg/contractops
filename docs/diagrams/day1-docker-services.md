# Day 1 — Docker Services

Developer workflow with `db` + `api` and `/health` check.

```mermaid
flowchart LR
    dev[Developer] -->|docker compose up --build| compose[Docker Compose]

    compose --> db[(db<br/>pgvector/pgvector:pg16<br/>5433:5432)]
    compose --> api[api<br/>FastAPI + Uvicorn<br/>8000:8000]

    api -->|depends_on: service_healthy<br/>DATABASE_URL @db:5432| db

    browser[Browser] -->|GET localhost:8000/health| api
    api -->|{"status": "ok"}| browser
```
