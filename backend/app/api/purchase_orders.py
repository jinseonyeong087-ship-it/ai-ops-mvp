import os
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

import psycopg
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["purchase-orders"])


class PurchaseOrderItemCreate(BaseModel):
    product_id: int = Field(ge=1)
    ordered_qty: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class PurchaseOrderCreateRequest(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=150)
    order_date: date
    expected_date: date | None = None
    warehouse_id: int = Field(ge=1)
    memo: str | None = None
    items: list[PurchaseOrderItemCreate] = Field(min_length=1)


class PurchaseOrderCreateResult(BaseModel):
    id: int
    po_number: str
    status: str
    total_amount: Decimal
    created_at: str


class PurchaseOrderStatusUpdateRequest(BaseModel):
    status: Literal["DRAFT", "SUBMITTED", "PARTIAL_RECEIVED", "RECEIVED", "CANCELED"]


def _get_db_url() -> str:
    raw = os.getenv("DATABASE_URL")
    if not raw:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")
    return raw.replace("+psycopg", "")


@router.post("/purchase-orders", status_code=status.HTTP_201_CREATED)
def create_purchase_order(payload: PurchaseOrderCreateRequest):
    db_url = _get_db_url()

    if payload.expected_date and payload.expected_date < payload.order_date:
        raise HTTPException(status_code=400, detail="expected_date must be >= order_date")

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM warehouses WHERE id = %s AND is_active = TRUE", (payload.warehouse_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Warehouse not found")

                product_ids = list({item.product_id for item in payload.items})
                cur.execute(
                    "SELECT id FROM products WHERE is_active = TRUE AND id = ANY(%s)",
                    (product_ids,),
                )
                valid_product_ids = {row[0] for row in cur.fetchall()}
                missing = sorted(set(product_ids) - valid_product_ids)
                if missing:
                    raise HTTPException(status_code=404, detail=f"Products not found: {missing}")

                cur.execute("SELECT nextval(pg_get_serial_sequence('purchase_orders', 'id'))")
                po_id = int(cur.fetchone()[0])
                po_number = f"PO-{payload.order_date.strftime('%Y%m%d')}-{po_id:06d}"

                cur.execute(
                    """
                    INSERT INTO purchase_orders (
                        id, po_number, supplier_name, status, order_date, expected_date,
                        warehouse_id, total_amount, memo, created_by
                    ) VALUES (%s, %s, %s, 'DRAFT', %s, %s, %s, 0, %s, %s)
                    RETURNING id, po_number, status, created_at
                    """,
                    (
                        po_id,
                        po_number,
                        payload.supplier_name,
                        payload.order_date,
                        payload.expected_date,
                        payload.warehouse_id,
                        payload.memo,
                        "system",
                    ),
                )
                po_row = cur.fetchone()

                total_amount = Decimal("0")
                for item in payload.items:
                    line_amount = (Decimal(item.ordered_qty) * item.unit_price).quantize(Decimal("0.01"))
                    total_amount += line_amount
                    cur.execute(
                        """
                        INSERT INTO purchase_order_items (
                            purchase_order_id, product_id, ordered_qty, received_qty, unit_price, line_amount
                        ) VALUES (%s, %s, %s, 0, %s, %s)
                        """,
                        (po_id, item.product_id, item.ordered_qty, item.unit_price, line_amount),
                    )

                total_amount = total_amount.quantize(Decimal("0.01"))
                cur.execute(
                    "UPDATE purchase_orders SET total_amount = %s, updated_at = now() WHERE id = %s",
                    (total_amount, po_id),
                )

    return {
        "data": PurchaseOrderCreateResult(
            id=po_row[0],
            po_number=po_row[1],
            status=po_row[2],
            total_amount=total_amount,
            created_at=po_row[3].isoformat(),
        ).model_dump(mode="json")
    }


@router.get("/purchase-orders")
def get_purchase_orders(
    status_filter: Literal["DRAFT", "SUBMITTED", "PARTIAL_RECEIVED", "RECEIVED", "CANCELED"] | None = Query(default=None, alias="status"),
    supplier_name: str | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    db_url = _get_db_url()
    offset = (page - 1) * size

    where_clauses: list[str] = []
    params: list = []

    if status_filter:
        where_clauses.append("po.status = %s")
        params.append(status_filter)

    if supplier_name:
        where_clauses.append("po.supplier_name ILIKE %s")
        params.append(f"%{supplier_name}%")

    if from_date:
        where_clauses.append("po.order_date >= %s")
        params.append(from_date)

    if to_date:
        where_clauses.append("po.order_date <= %s")
        params.append(to_date)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM purchase_orders po {where_sql}", params)
            total = int(cur.fetchone()[0])

            cur.execute(
                f"""
                SELECT
                    po.id,
                    po.po_number,
                    po.supplier_name,
                    po.status,
                    po.order_date,
                    po.expected_date,
                    po.total_amount,
                    po.warehouse_id
                FROM purchase_orders po
                {where_sql}
                ORDER BY po.order_date DESC, po.id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, size, offset],
            )
            rows = cur.fetchall()

    data = [
        {
            "id": row[0],
            "po_number": row[1],
            "supplier_name": row[2],
            "status": row[3],
            "order_date": row[4].isoformat() if row[4] else None,
            "expected_date": row[5].isoformat() if row[5] else None,
            "total_amount": float(row[6] or 0),
            "warehouse_id": row[7],
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


@router.get("/purchase-orders/{po_id}")
def get_purchase_order_detail(po_id: int):
    db_url = _get_db_url()

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    po.id,
                    po.po_number,
                    po.supplier_name,
                    po.status,
                    po.order_date,
                    po.expected_date,
                    po.warehouse_id,
                    po.total_amount,
                    po.memo,
                    po.created_by,
                    po.created_at,
                    po.updated_at
                FROM purchase_orders po
                WHERE po.id = %s
                """,
                (po_id,),
            )
            po_row = cur.fetchone()

            if not po_row:
                raise HTTPException(status_code=404, detail="Purchase order not found")

            cur.execute(
                """
                SELECT
                    poi.id,
                    poi.product_id,
                    p.sku,
                    p.name,
                    poi.ordered_qty,
                    poi.received_qty,
                    poi.unit_price,
                    poi.line_amount
                FROM purchase_order_items poi
                JOIN products p ON p.id = poi.product_id
                WHERE poi.purchase_order_id = %s
                ORDER BY poi.id ASC
                """,
                (po_id,),
            )
            item_rows = cur.fetchall()

    items = [
        {
            "id": row[0],
            "product_id": row[1],
            "sku": row[2],
            "name": row[3],
            "ordered_qty": row[4],
            "received_qty": row[5],
            "unit_price": float(row[6] or 0),
            "line_amount": float(row[7] or 0),
        }
        for row in item_rows
    ]

    return {
        "data": {
            "id": po_row[0],
            "po_number": po_row[1],
            "supplier_name": po_row[2],
            "status": po_row[3],
            "order_date": po_row[4].isoformat() if po_row[4] else None,
            "expected_date": po_row[5].isoformat() if po_row[5] else None,
            "warehouse_id": po_row[6],
            "total_amount": float(po_row[7] or 0),
            "memo": po_row[8],
            "created_by": po_row[9],
            "created_at": po_row[10].isoformat() if po_row[10] else None,
            "updated_at": po_row[11].isoformat() if po_row[11] else None,
            "items": items,
        }
    }


@router.patch("/purchase-orders/{po_id}/status")
def update_purchase_order_status(po_id: int, payload: PurchaseOrderStatusUpdateRequest):
    db_url = _get_db_url()

    allowed_transitions = {
        "DRAFT": {"SUBMITTED", "CANCELED"},
        "SUBMITTED": {"PARTIAL_RECEIVED", "RECEIVED", "CANCELED"},
        "PARTIAL_RECEIVED": {"RECEIVED", "CANCELED"},
        "RECEIVED": set(),
        "CANCELED": set(),
    }

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT status FROM purchase_orders WHERE id = %s FOR UPDATE",
                    (po_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Purchase order not found")

                current_status = row[0]
                target_status = payload.status

                if current_status == target_status:
                    cur.execute(
                        "SELECT id, status, updated_at FROM purchase_orders WHERE id = %s",
                        (po_id,),
                    )
                    current = cur.fetchone()
                    return {
                        "data": {
                            "id": current[0],
                            "status": current[1],
                            "updated_at": current[2].isoformat() if current[2] else None,
                        }
                    }

                if target_status not in allowed_transitions.get(current_status, set()):
                    raise HTTPException(
                        status_code=409,
                        detail=f"Invalid status transition: {current_status} -> {target_status}",
                    )

                cur.execute(
                    """
                    UPDATE purchase_orders
                    SET status = %s,
                        updated_at = now()
                    WHERE id = %s
                    RETURNING id, status, updated_at
                    """,
                    (target_status, po_id),
                )
                updated = cur.fetchone()

    return {
        "data": {
            "id": updated[0],
            "status": updated[1],
            "updated_at": updated[2].isoformat() if updated[2] else None,
        }
    }


class PurchaseOrderReceiveItem(BaseModel):
    product_id: int = Field(ge=1)
    received_qty: int = Field(gt=0)


class PurchaseOrderReceiveRequest(BaseModel):
    received_at: datetime | None = None
    items: list[PurchaseOrderReceiveItem] = Field(min_length=1)
    note: str | None = None


@router.post("/purchase-orders/{po_id}/receive")
def receive_purchase_order(po_id: int, payload: PurchaseOrderReceiveRequest):
    db_url = _get_db_url()

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, status, warehouse_id
                    FROM purchase_orders
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (po_id,),
                )
                po = cur.fetchone()
                if not po:
                    raise HTTPException(status_code=404, detail="Purchase order not found")

                _, po_status, warehouse_id = po
                if po_status not in {"SUBMITTED", "PARTIAL_RECEIVED"}:
                    raise HTTPException(status_code=409, detail=f"Cannot receive in status: {po_status}")

                cur.execute(
                    """
                    SELECT id, product_id, ordered_qty, received_qty
                    FROM purchase_order_items
                    WHERE purchase_order_id = %s
                    FOR UPDATE
                    """,
                    (po_id,),
                )
                po_items = cur.fetchall()
                item_map = {row[1]: {"id": row[0], "ordered_qty": row[2], "received_qty": row[3]} for row in po_items}

                requested_product_ids = [item.product_id for item in payload.items]
                unknown_products = sorted(set(requested_product_ids) - set(item_map.keys()))
                if unknown_products:
                    raise HTTPException(status_code=400, detail=f"Products not in purchase order: {unknown_products}")

                total_received_qty = 0
                movement_time = payload.received_at or datetime.now()

                for req_item in payload.items:
                    item_info = item_map[req_item.product_id]
                    new_received = item_info["received_qty"] + req_item.received_qty
                    if new_received > item_info["ordered_qty"]:
                        raise HTTPException(
                            status_code=409,
                            detail=(
                                f"Received qty exceeds ordered qty for product_id={req_item.product_id}: "
                                f"ordered={item_info['ordered_qty']}, current_received={item_info['received_qty']}, "
                                f"request={req_item.received_qty}"
                            ),
                        )

                    cur.execute(
                        """
                        UPDATE purchase_order_items
                        SET received_qty = %s,
                            updated_at = now()
                        WHERE id = %s
                        """,
                        (new_received, item_info["id"]),
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
                            note,
                            moved_at
                        ) VALUES (%s, %s, 'INBOUND', %s, 'PO', %s, %s, %s)
                        """,
                        (
                            req_item.product_id,
                            warehouse_id,
                            req_item.received_qty,
                            str(po_id),
                            payload.note,
                            movement_time,
                        ),
                    )

                    cur.execute(
                        """
                        SELECT id, on_hand_qty, reserved_qty, available_qty
                        FROM inventory_snapshots
                        WHERE product_id = %s AND warehouse_id = %s
                        FOR UPDATE
                        """,
                        (req_item.product_id, warehouse_id),
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
                            (req_item.product_id, warehouse_id),
                        )
                        snapshot = cur.fetchone()

                    snapshot_id, on_hand_qty, reserved_qty, available_qty = snapshot
                    new_on_hand_qty = on_hand_qty + req_item.received_qty
                    new_available_qty = available_qty + req_item.received_qty

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

                    total_received_qty += req_item.received_qty

                cur.execute(
                    """
                    SELECT
                        COALESCE(SUM(ordered_qty), 0) AS total_ordered_qty,
                        COALESCE(SUM(received_qty), 0) AS total_received_qty
                    FROM purchase_order_items
                    WHERE purchase_order_id = %s
                    """,
                    (po_id,),
                )
                total_ordered_qty, cumulative_received_qty = cur.fetchone()

                new_status = "PARTIAL_RECEIVED"
                if int(cumulative_received_qty or 0) >= int(total_ordered_qty or 0):
                    new_status = "RECEIVED"

                cur.execute(
                    """
                    UPDATE purchase_orders
                    SET status = %s,
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (new_status, po_id),
                )

    return {
        "data": {
            "po_id": po_id,
            "status": new_status,
            "received_items": len(payload.items),
            "received_total_qty": total_received_qty,
        }
    }
