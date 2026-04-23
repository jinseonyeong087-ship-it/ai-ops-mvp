import os
from datetime import date
from decimal import Decimal

import psycopg
from fastapi import APIRouter, HTTPException, status
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
