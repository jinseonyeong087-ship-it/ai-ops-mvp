import os
from datetime import date, datetime
from typing import Literal

import psycopg
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["inventory"])


class InventoryMovementCreate(BaseModel):
    product_id: int = Field(ge=1)
    warehouse_id: int = Field(ge=1)
    movement_type: Literal["INBOUND", "OUTBOUND", "ADJUSTMENT", "RETURN"]
    qty: int = Field(gt=0)
    reference_type: str | None = Field(default=None, max_length=30)
    reference_id: str | None = Field(default=None, max_length=100)
    note: str | None = None


class InventoryMovementCreateResponse(BaseModel):
    movement_id: int
    product_id: int
    warehouse_id: int
    movement_type: str
    qty: int
    moved_at: datetime


def _get_db_url() -> str:
    raw = os.getenv("DATABASE_URL")
    if not raw:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")
    return raw.replace("+psycopg", "")


@router.get("/inventory/items")
def get_inventory_items(
    q: str | None = Query(default=None, description="SKU or product name"),
    category: str | None = Query(default=None),
    warehouse_id: int | None = Query(default=None, ge=1),
    stock_status: Literal["NORMAL", "LOW", "OUT"] | None = Query(default=None),
    sort: Literal["name", "available_qty", "updated_at"] = Query(default="updated_at"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    db_url = _get_db_url()
    offset = (page - 1) * size

    where_clauses: list[str] = ["p.is_active = TRUE"]
    params: list = []

    if q:
        where_clauses.append("(p.sku ILIKE %s OR p.name ILIKE %s)")
        keyword = f"%{q}%"
        params.extend([keyword, keyword])

    if category:
        where_clauses.append("p.category = %s")
        params.append(category)

    if warehouse_id:
        where_clauses.append("w.id = %s")
        params.append(warehouse_id)

    if stock_status == "LOW":
        where_clauses.append("inv.available_qty > 0 AND inv.available_qty <= p.reorder_point")
    elif stock_status == "OUT":
        where_clauses.append("inv.available_qty <= 0")
    elif stock_status == "NORMAL":
        where_clauses.append("inv.available_qty > p.reorder_point")

    where_sql = " AND ".join(where_clauses)

    order_by_map = {
        "name": "p.name",
        "available_qty": "inv.available_qty",
        "updated_at": "inv.updated_at",
    }
    order_by = order_by_map[sort]
    direction = "ASC" if order == "asc" else "DESC"

    base_from_sql = f"""
        FROM inventory_snapshots inv
        JOIN products p ON p.id = inv.product_id
        JOIN warehouses w ON w.id = inv.warehouse_id
        WHERE {where_sql}
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) {base_from_sql}", params)
            total = int(cur.fetchone()[0])

            cur.execute(
                f"""
                SELECT
                    p.id AS product_id,
                    p.sku,
                    p.name,
                    p.category,
                    w.id AS warehouse_id,
                    w.name AS warehouse_name,
                    inv.on_hand_qty,
                    inv.reserved_qty,
                    inv.available_qty,
                    p.safety_stock,
                    p.reorder_point,
                    CASE
                      WHEN inv.available_qty <= 0 THEN 'OUT'
                      WHEN inv.available_qty <= p.reorder_point THEN 'LOW'
                      ELSE 'NORMAL'
                    END AS stock_status,
                    inv.updated_at
                {base_from_sql}
                ORDER BY {order_by} {direction}, p.id ASC
                LIMIT %s OFFSET %s
                """,
                [*params, size, offset],
            )
            rows = cur.fetchall()

    data = [
        {
            "product_id": row[0],
            "sku": row[1],
            "name": row[2],
            "category": row[3],
            "warehouse_id": row[4],
            "warehouse_name": row[5],
            "on_hand_qty": row[6],
            "reserved_qty": row[7],
            "available_qty": row[8],
            "safety_stock": row[9],
            "reorder_point": row[10],
            "stock_status": row[11],
            "updated_at": row[12].isoformat() if row[12] else None,
        }
        for row in rows
    ]

    return {
        "data": data,
        "meta": {
            "page": page,
            "size": size,
            "total": total,
        },
    }


@router.post("/inventory/movements", status_code=status.HTTP_201_CREATED)
def create_inventory_movement(payload: InventoryMovementCreate):
    db_url = _get_db_url()

    delta = payload.qty
    if payload.movement_type == "OUTBOUND":
        delta = -payload.qty

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM products WHERE id = %s AND is_active = TRUE", (payload.product_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Product not found")

                cur.execute("SELECT id FROM warehouses WHERE id = %s AND is_active = TRUE", (payload.warehouse_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Warehouse not found")

                cur.execute(
                    """
                    SELECT id, on_hand_qty, reserved_qty, available_qty
                    FROM inventory_snapshots
                    WHERE product_id = %s AND warehouse_id = %s
                    FOR UPDATE
                    """,
                    (payload.product_id, payload.warehouse_id),
                )
                snapshot = cur.fetchone()

                if not snapshot:
                    cur.execute(
                        """
                        INSERT INTO inventory_snapshots (
                            product_id, warehouse_id, on_hand_qty, reserved_qty, available_qty
                        ) VALUES (%s, %s, 0, 0, 0)
                        RETURNING id, on_hand_qty, reserved_qty, available_qty
                        """,
                        (payload.product_id, payload.warehouse_id),
                    )
                    snapshot = cur.fetchone()

                snapshot_id, on_hand_qty, reserved_qty, available_qty = snapshot

                if payload.movement_type == "OUTBOUND" and available_qty < payload.qty:
                    raise HTTPException(status_code=409, detail="Insufficient available stock")

                new_on_hand_qty = on_hand_qty + delta
                new_available_qty = available_qty + delta

                cur.execute(
                    """
                    UPDATE inventory_snapshots
                    SET on_hand_qty = %s,
                        reserved_qty = %s,
                        available_qty = %s,
                        snapshot_at = now(),
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (new_on_hand_qty, reserved_qty, new_available_qty, snapshot_id),
                )

                cur.execute(
                    """
                    INSERT INTO stock_movements (
                        product_id,
                        warehouse_id,
                        movement_type,
                        qty,
                        reference_type,
                        reference_id,
                        note
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, moved_at
                    """,
                    (
                        payload.product_id,
                        payload.warehouse_id,
                        payload.movement_type,
                        payload.qty,
                        payload.reference_type,
                        payload.reference_id,
                        payload.note,
                    ),
                )
                movement_id, moved_at = cur.fetchone()

    return {
        "data": InventoryMovementCreateResponse(
            movement_id=movement_id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            movement_type=payload.movement_type,
            qty=payload.qty,
            moved_at=moved_at,
        ).model_dump(mode="json")
    }


@router.get("/inventory/movements")
def get_inventory_movements(
    product_id: int | None = Query(default=None, ge=1),
    warehouse_id: int | None = Query(default=None, ge=1),
    movement_type: Literal["INBOUND", "OUTBOUND", "ADJUSTMENT", "RETURN"] | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    db_url = _get_db_url()
    offset = (page - 1) * size

    where_clauses: list[str] = []
    params: list = []

    if product_id:
        where_clauses.append("sm.product_id = %s")
        params.append(product_id)

    if warehouse_id:
        where_clauses.append("sm.warehouse_id = %s")
        params.append(warehouse_id)

    if movement_type:
        where_clauses.append("sm.movement_type = %s")
        params.append(movement_type)

    if from_date:
        where_clauses.append("sm.moved_at::date >= %s")
        params.append(from_date)

    if to_date:
        where_clauses.append("sm.moved_at::date <= %s")
        params.append(to_date)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM stock_movements sm {where_sql}", params)
            total = int(cur.fetchone()[0])

            cur.execute(
                f"""
                SELECT
                    sm.id,
                    sm.product_id,
                    sm.warehouse_id,
                    sm.movement_type,
                    sm.qty,
                    sm.reference_type,
                    sm.reference_id,
                    sm.note,
                    sm.moved_at
                FROM stock_movements sm
                {where_sql}
                ORDER BY sm.moved_at DESC, sm.id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, size, offset],
            )
            rows = cur.fetchall()

    data = [
        {
            "id": row[0],
            "product_id": row[1],
            "warehouse_id": row[2],
            "movement_type": row[3],
            "qty": row[4],
            "reference_type": row[5],
            "reference_id": row[6],
            "note": row[7],
            "moved_at": row[8].isoformat() if row[8] else None,
        }
        for row in rows
    ]

    return {
        "data": data,
        "meta": {
            "page": page,
            "size": size,
            "total": total,
        },
    }
