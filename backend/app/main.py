from fastapi import FastAPI

from .auth import admin_router, router as auth_router

app = FastAPI(title="ContractOps API")
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}
