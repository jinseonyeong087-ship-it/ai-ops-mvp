import os
from datetime import date, timedelta

import psycopg
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["kpi"])


def _get_db_url() -> str:
    raw = os.getenv("DATABASE_URL")
    if not raw:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")
    return raw.replace("+psycopg", "")


@router.get("/kpi/summary")
def get_kpi_summary(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    warehouse_id: int | None = Query(default=None),
):
    end_date = to_date or date.today()
    start_date = from_date or (end_date - timedelta(days=29))

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    period_days = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_days - 1)

    db_url = _get_db_url()

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Inventory KPI
            inv_params: tuple = tuple()
            if warehouse_id:
                inv_join = "LEFT JOIN inventory_snapshots i ON i.product_id = p.id AND i.warehouse_id = %s"
                inv_params = (warehouse_id,)
            else:
                inv_join = "LEFT JOIN inventory_snapshots i ON i.product_id = p.id"

            cur.execute(
                f"""
                SELECT
                  COUNT(DISTINCT p.id) AS total_sku,
                  COALESCE(SUM(i.on_hand_qty), 0) AS total_on_hand_qty,
                  COUNT(DISTINCT CASE WHEN i.available_qty > 0 AND i.available_qty <= p.reorder_point THEN p.id END) AS low_stock_sku,
                  COUNT(DISTINCT CASE WHEN i.available_qty <= 0 THEN p.id END) AS out_of_stock_sku
                FROM products p
                {inv_join}
                WHERE p.is_active = TRUE
                """,
                inv_params,
            )
            total_sku, total_on_hand_qty, low_stock_sku, out_of_stock_sku = cur.fetchone()

            # Purchase KPI
            po_where = ["order_date BETWEEN %s AND %s"]
            po_params: list = [start_date, end_date]
            if warehouse_id:
                po_where.append("warehouse_id = %s")
                po_params.append(warehouse_id)

            cur.execute(
                f"""
                SELECT
                  COUNT(*) FILTER (WHERE status = 'DRAFT') AS draft_count,
                  COUNT(*) FILTER (WHERE status = 'SUBMITTED') AS submitted_count,
                  COUNT(*) FILTER (WHERE status = 'PARTIAL_RECEIVED') AS partial_received_count,
                  COUNT(*) FILTER (
                    WHERE status IN ('SUBMITTED', 'PARTIAL_RECEIVED')
                      AND expected_date IS NOT NULL
                      AND expected_date < CURRENT_DATE
                  ) AS overdue_count
                FROM purchase_orders
                WHERE {' AND '.join(po_where)}
                """,
                po_params,
            )
            draft_count, submitted_count, partial_received_count, overdue_count = cur.fetchone()

            # Sales KPI (current)
            cur.execute(
                """
                SELECT
                  COALESCE(SUM(gross_sales), 0),
                  COALESCE(SUM(net_sales), 0),
                  COALESCE(SUM(order_count), 0)
                FROM sales_daily
                WHERE sales_date BETWEEN %s AND %s
                """,
                (start_date, end_date),
            )
            gross_sales, net_sales, order_count = cur.fetchone()

            # Sales KPI (previous period for growth)
            cur.execute(
                """
                SELECT COALESCE(SUM(net_sales), 0)
                FROM sales_daily
                WHERE sales_date BETWEEN %s AND %s
                """,
                (prev_start, prev_end),
            )
            prev_net_sales = cur.fetchone()[0]

            if prev_net_sales and float(prev_net_sales) != 0:
                growth_rate_pct = round((float(net_sales) - float(prev_net_sales)) / float(prev_net_sales) * 100, 2)
            else:
                growth_rate_pct = 0.0

            # Logistics KPI
            lm_where = ["moved_at::date BETWEEN %s AND %s"]
            lm_params: list = [start_date, end_date]
            if warehouse_id:
                lm_where.append("warehouse_id = %s")
                lm_params.append(warehouse_id)

            cur.execute(
                f"""
                SELECT
                  COALESCE(SUM(CASE WHEN movement_type = 'INBOUND' THEN qty ELSE 0 END), 0) AS inbound_qty,
                  COALESCE(SUM(CASE WHEN movement_type = 'OUTBOUND' THEN qty ELSE 0 END), 0) AS outbound_qty
                FROM stock_movements
                WHERE {' AND '.join(lm_where)}
                """,
                lm_params,
            )
            inbound_qty, outbound_qty = cur.fetchone()

    return {
        "data": {
            "inventory": {
                "total_sku": int(total_sku or 0),
                "total_on_hand_qty": int(total_on_hand_qty or 0),
                "low_stock_sku": int(low_stock_sku or 0),
                "out_of_stock_sku": int(out_of_stock_sku or 0),
            },
            "purchase": {
                "draft_count": int(draft_count or 0),
                "submitted_count": int(submitted_count or 0),
                "partial_received_count": int(partial_received_count or 0),
                "overdue_count": int(overdue_count or 0),
            },
            "sales": {
                "gross_sales": float(gross_sales or 0),
                "net_sales": float(net_sales or 0),
                "order_count": int(order_count or 0),
                "growth_rate_pct": growth_rate_pct,
            },
            "logistics": {
                "inbound_qty": int(inbound_qty or 0),
                "outbound_qty": int(outbound_qty or 0),
            },
        },
        "meta": {
            "from": str(start_date),
            "to": str(end_date),
            "warehouse_id": warehouse_id,
        },
    }
