"""애플리케이션 진입점.

역할:
- FastAPI 앱 생성
- 라우터 등록
- 공통 에러 응답 포맷 표준화
"""

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
    """입력값 검증 실패를 공통 포맷으로 반환한다."""
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
    """HTTP 상태코드를 내부 표준 에러코드로 매핑한다."""
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
    """FastAPI HTTPException 처리."""
    return _http_error_response(exc.status_code, str(exc.detail))


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException):
    """라우팅 404 등 Starlette 예외 처리."""
    return _http_error_response(exc.status_code, str(exc.detail))


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception):
    """미처리 예외는 내부에 숨기고 표준 500 응답으로 반환한다."""
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


# 라우터 등록 순서: 공통 -> 도메인 API
app.include_router(health_router)
app.include_router(ops_router, prefix="/api")
app.include_router(kpi_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(purchase_orders_router, prefix="/api")
