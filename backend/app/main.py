from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import admin_router, router as auth_router
from .routers.contracts import router as contracts_router

app = FastAPI(title="ContractOps API")

# React dev server (Vite) on port 5173 — explicit origins only, never "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(contracts_router)


@app.get("/health")
def health():
    return {"status": "ok"}
