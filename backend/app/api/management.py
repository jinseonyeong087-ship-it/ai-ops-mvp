"""상품 등록 / 스케줄 / 판매현황 보조 API.

프론트 대시보드 화면에서 사용하는 단순 CRUD 중심 엔드포인트.
"""

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

import psycopg
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["management"])


def _get_db_url() -> str:
    raw = os.getenv("DATABASE_URL")
    if not raw:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")
    return raw.replace("+psycopg", "")


class ProductCreateRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    category: Literal["과일", "채소", "유제품", "육류", "간편식", "기타"] = "기타"
    unit: Literal["ea", "box", "kg", "pack"] = "ea"
    safety_stock: int = Field(ge=0, default=0)
    reorder_point: int = Field(ge=0, default=0)
    warehouse_id: int = Field(ge=1)
    initial_qty: int = Field(ge=0, default=0)


class SalesUpsertRequest(BaseModel):
    sales_date: date
    channel: Literal["ALL", "ONLINE", "OFFLINE", "B2B"] = "ALL"
    order_count: int = Field(ge=0, default=0)
    item_qty: int = Field(ge=0, default=0)
    gross_sales: Decimal = Field(ge=0, default=0)
    discount_amount: Decimal = Field(ge=0, default=0)


class ScheduleCreateRequest(BaseModel):
    job_name: str = Field(min_length=1, max_length=120)
    job_type: Literal["REPORT", "SYNC", "ALERT"] = "REPORT"
    status: Literal["PENDING", "RUNNING", "DONE"] = "PENDING"
    next_run_at: datetime
    payload_note: str | None = None


@router.get("/meta/options")
def get_meta_options():
    db_url = _get_db_url()

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM warehouses WHERE is_active = TRUE ORDER BY id")
            warehouses = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]

    return {
        "data": {
            "categories": ["과일", "채소", "유제품", "육류", "간편식", "기타"],
            "units": ["ea", "box", "kg", "pack"],
            "channels": ["ALL", "ONLINE", "OFFLINE", "B2B"],
            "job_types": ["REPORT", "SYNC", "ALERT"],
            "job_statuses": ["PENDING", "RUNNING", "DONE"],
            "warehouses": warehouses,
        }
    }


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreateRequest):
    db_url = _get_db_url()

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM warehouses WHERE id = %s AND is_active = TRUE", (payload.warehouse_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Warehouse not found")

                cur.execute("SELECT id FROM products WHERE sku = %s", (payload.sku,))
                if cur.fetchone():
                    raise HTTPException(status_code=409, detail="SKU already exists")

                cur.execute(
                    """
                    INSERT INTO products (sku, name, category, unit, safety_stock, reorder_point, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id, created_at
                    """,
                    (
                        payload.sku,
                        payload.name,
                        payload.category,
                        payload.unit,
                        payload.safety_stock,
                        payload.reorder_point,
                    ),
                )
                product_id, created_at = cur.fetchone()

                cur.execute(
                    """
                    INSERT INTO inventory_snapshots (product_id, warehouse_id, on_hand_qty, reserved_qty, available_qty)
                    VALUES (%s, %s, %s, 0, %s)
                    ON CONFLICT (product_id, warehouse_id)
                    DO UPDATE SET
                      on_hand_qty = EXCLUDED.on_hand_qty,
                      available_qty = EXCLUDED.available_qty,
                      updated_at = now()
                    """,
                    (product_id, payload.warehouse_id, payload.initial_qty, payload.initial_qty),
                )

    return {
        "data": {
            "id": product_id,
            "sku": payload.sku,
            "name": payload.name,
            "warehouse_id": payload.warehouse_id,
            "initial_qty": payload.initial_qty,
            "created_at": created_at.isoformat() if created_at else None,
        }
    }


@router.get("/sales/daily")
def get_sales_daily(page: int = Query(default=1, ge=1), size: int = Query(default=15, ge=1, le=100)):
    db_url = _get_db_url()
    offset = (page - 1) * size

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sales_daily")
            total = int(cur.fetchone()[0])

            cur.execute(
                """
                SELECT sales_date, channel, order_count, item_qty, gross_sales, discount_amount, net_sales
                FROM sales_daily
                ORDER BY sales_date DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (size, offset),
            )
            rows = cur.fetchall()

    data = [
        {
            "sales_date": row[0].isoformat() if row[0] else None,
            "channel": row[1],
            "order_count": row[2],
            "item_qty": row[3],
            "gross_sales": float(row[4] or 0),
            "discount_amount": float(row[5] or 0),
            "net_sales": float(row[6] or 0),
        }
        for row in rows
    ]

    return {"data": data, "meta": {"page": page, "size": size, "total": total}}


@router.post("/sales/daily", status_code=status.HTTP_201_CREATED)
def upsert_sales_daily(payload: SalesUpsertRequest):
    db_url = _get_db_url()
    net_sales = (payload.gross_sales - payload.discount_amount).quantize(Decimal("0.01"))

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sales_daily (sales_date, channel, order_count, item_qty, gross_sales, discount_amount, net_sales)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sales_date, channel)
                    DO UPDATE SET
                      order_count = EXCLUDED.order_count,
                      item_qty = EXCLUDED.item_qty,
                      gross_sales = EXCLUDED.gross_sales,
                      discount_amount = EXCLUDED.discount_amount,
                      net_sales = EXCLUDED.net_sales,
                      updated_at = now()
                    RETURNING id
                    """,
                    (
                        payload.sales_date,
                        payload.channel,
                        payload.order_count,
                        payload.item_qty,
                        payload.gross_sales,
                        payload.discount_amount,
                        net_sales,
                    ),
                )
                sales_id = int(cur.fetchone()[0])

    return {"data": {"id": sales_id, "sales_date": str(payload.sales_date), "channel": payload.channel}}


@router.get("/schedules")
def get_schedules(page: int = Query(default=1, ge=1), size: int = Query(default=15, ge=1, le=100)):
    db_url = _get_db_url()
    offset = (page - 1) * size

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM automation_jobs")
            total = int(cur.fetchone()[0])

            cur.execute(
                """
                SELECT id, job_name, job_type, status, next_run_at, payload
                FROM automation_jobs
                ORDER BY next_run_at ASC NULLS LAST, id DESC
                LIMIT %s OFFSET %s
                """,
                (size, offset),
            )
            rows = cur.fetchall()

    data = [
        {
            "id": row[0],
            "job_name": row[1],
            "job_type": row[2],
            "status": row[3],
            "next_run_at": row[4].isoformat() if row[4] else None,
            "payload": row[5] or {},
        }
        for row in rows
    ]

    return {"data": data, "meta": {"page": page, "size": size, "total": total}}


@router.post("/schedules", status_code=status.HTTP_201_CREATED)
def create_schedule(payload: ScheduleCreateRequest):
    db_url = _get_db_url()

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO automation_jobs (job_name, job_type, status, next_run_at, payload)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    RETURNING id, created_at
                    """,
                    (
                        payload.job_name,
                        payload.job_type,
                        payload.status,
                        payload.next_run_at,
                        '{"note": "%s"}' % ((payload.payload_note or "").replace('"', "'")),
                    ),
                )
                schedule_id, created_at = cur.fetchone()

    return {
        "data": {
            "id": int(schedule_id),
            "job_name": payload.job_name,
            "job_type": payload.job_type,
            "status": payload.status,
            "next_run_at": payload.next_run_at.isoformat(),
            "created_at": created_at.isoformat() if created_at else None,
        }
    }
