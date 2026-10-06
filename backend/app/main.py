from fastapi import FastAPI

app = FastAPI(title="ContractOps API - Day 1 skeleton")


@app.get("/health")
def health():
    return {"status": "ok"}
