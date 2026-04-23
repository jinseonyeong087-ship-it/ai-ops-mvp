from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.health import router as health_router
from app.api.inventory import router as inventory_router
from app.api.kpi import router as kpi_router
from app.api.ops import router as ops_router
from app.api.purchase_orders import router as purchase_orders_router

app = FastAPI(title="AI Ops MVP", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "invalid request",
                "details": exc.errors(),
            }
        },
    )


def _http_error_response(status_code: int, detail: str):
    if status_code == 404:
        code = "NOT_FOUND"
    elif status_code == 409:
        code = "CONFLICT"
    elif status_code == 400:
        code = "VALIDATION_ERROR"
    else:
        code = "INTERNAL_ERROR" if status_code >= 500 else "HTTP_ERROR"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": str(detail),
                "details": [],
            }
        },
    )


@app.exception_handler(HTTPException)
async def fastapi_http_exception_handler(_: Request, exc: HTTPException):
    return _http_error_response(exc.status_code, str(exc.detail))


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException):
    return _http_error_response(exc.status_code, str(exc.detail))


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "internal server error",
                "details": [],
            }
        },
    )


app.include_router(health_router)
app.include_router(ops_router, prefix="/api")
app.include_router(kpi_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(purchase_orders_router, prefix="/api")
