from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.ops import router as ops_router

app = FastAPI(title="AI Ops MVP", version="0.1.0")

app.include_router(health_router)
app.include_router(ops_router, prefix="/api")
