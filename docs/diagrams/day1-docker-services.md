# Day 1 - Docker Services

Developer workflow with db + api and the /health check.

````mermaid
flowchart LR
    dev["Developer"] -->|"docker compose up --build"| compose["Docker Compose"]
    compose --> db[("db - pgvector pg16 - port 5433")]
    compose --> api["api - FastAPI + Uvicorn - port 8000"]
    api -->|"waits until db is healthy"| db
    browser["Browser"] -->|"GET /health"| api
    api -->|"status ok"| browser
````
