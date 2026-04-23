from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.ops import router as ops_router
from app.api.kpi import router as kpi_router
from app.api.inventory import router as inventory_router
from app.api.purchase_orders import router as purchase_orders_router

app = FastAPI(title="AI Ops MVP", version="0.1.0")

app.include_router(health_router)
app.include_router(ops_router, prefix="/api")
app.include_router(kpi_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(purchase_orders_router, prefix="/api")
