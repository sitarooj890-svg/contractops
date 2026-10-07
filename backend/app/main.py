from fastapi import FastAPI

from .auth import router as auth_router

app = FastAPI(title="ContractOps API - Day 1 skeleton")
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}
