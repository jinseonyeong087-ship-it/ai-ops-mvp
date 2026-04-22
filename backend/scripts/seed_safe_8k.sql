-- AI Ops MVP safe seed (~8k rows)
-- Dev-only. Run after alembic migration.

BEGIN;

-- Reset (dev only)
TRUNCATE TABLE
  purchase_order_items,
  stock_movements,
  inventory_snapshots,
  purchase_orders,
  sales_daily,
  automation_jobs,
  ai_query_logs,
  products,
  warehouses
RESTART IDENTITY CASCADE;

-- 1) Warehouses (2)
INSERT INTO warehouses (code, name, location, is_active)
VALUES
  ('WH-SEOUL', '서울 메인창고', '서울', TRUE),
  ('WH-BUSAN', '부산 서브창고', '부산', TRUE);

-- 2) Products (200)
INSERT INTO products (sku, name, category, unit, safety_stock, reorder_point, is_active)
SELECT
  format('SKU-%04s', gs),
  format('상품 %s', gs),
  (ARRAY['식품','생활','뷰티','가전','패션'])[(gs % 5) + 1],
  'ea',
  (5 + (gs % 20)),
  (10 + (gs % 30)),
  TRUE
FROM generate_series(1, 200) gs;

-- 3) Inventory snapshots (400 = 200 products x 2 warehouses)
INSERT INTO inventory_snapshots (product_id, warehouse_id, on_hand_qty, reserved_qty, available_qty)
SELECT
  p.id,
  w.id,
  (50 + ((p.id * 7 + w.id * 11) % 300))::int as on_hand_qty,
  ((p.id * 3 + w.id) % 40)::int as reserved_qty,
  (50 + ((p.id * 7 + w.id * 11) % 300) - ((p.id * 3 + w.id) % 40))::int as available_qty
FROM products p
CROSS JOIN warehouses w;

-- 4) Stock movements (5000)
INSERT INTO stock_movements (
  product_id, warehouse_id, movement_type, qty,
  reference_type, reference_id, note, moved_at
)
SELECT
  ((gs - 1) % 200) + 1 as product_id,
  ((gs - 1) % 2) + 1 as warehouse_id,
  (ARRAY['INBOUND','OUTBOUND','ADJUSTMENT','RETURN'])[((gs - 1) % 4) + 1] as movement_type,
  (1 + (gs % 40))::int as qty,
  (ARRAY['PO','SALE','MANUAL','SYNC'])[((gs - 1) % 4) + 1] as reference_type,
  format('REF-%06s', gs),
  'seed movement',
  now() - ((gs % 90) || ' days')::interval - ((gs % 24) || ' hours')::interval
FROM generate_series(1, 5000) gs;

-- 5) Purchase orders (300)
INSERT INTO purchase_orders (
  po_number, supplier_name, status, order_date, expected_date,
  warehouse_id, total_amount, memo, created_by
)
SELECT
  format('PO-2026-%04s', gs),
  (ARRAY['A공급사','B공급사','C공급사','D공급사'])[((gs - 1) % 4) + 1],
  (ARRAY['DRAFT','SUBMITTED','PARTIAL_RECEIVED','RECEIVED','CANCELED'])[((gs - 1) % 5) + 1],
  (current_date - ((gs % 120) || ' days')::interval)::date,
  (current_date + (((gs % 20) - 5) || ' days')::interval)::date,
  ((gs - 1) % 2) + 1,
  0,
  'seed po',
  'seed'
FROM generate_series(1, 300) gs;

-- 6) Purchase order items (1200 = 300 orders x 4 lines)
INSERT INTO purchase_order_items (
  purchase_order_id, product_id, ordered_qty, received_qty,
  unit_price, line_amount
)
SELECT
  po.id,
  (((po.id * 13 + k * 17) % 200) + 1) as product_id,
  (5 + ((po.id + k) % 40))::int as ordered_qty,
  CASE
    WHEN po.status = 'RECEIVED' THEN (5 + ((po.id + k) % 40))::int
    WHEN po.status = 'PARTIAL_RECEIVED' THEN ((5 + ((po.id + k) % 40)) / 2)::int
    ELSE 0
  END as received_qty,
  (1000 + ((po.id * 71 + k * 19) % 9000))::numeric(12,2) as unit_price,
  ((5 + ((po.id + k) % 40)) * (1000 + ((po.id * 71 + k * 19) % 9000)))::numeric(14,2) as line_amount
FROM purchase_orders po
CROSS JOIN generate_series(1, 4) k;

-- sync purchase_orders.total_amount
UPDATE purchase_orders p
SET total_amount = x.sum_amount
FROM (
  SELECT purchase_order_id, SUM(line_amount)::numeric(14,2) as sum_amount
  FROM purchase_order_items
  GROUP BY purchase_order_id
) x
WHERE p.id = x.purchase_order_id;

-- 7) Sales daily (365)
INSERT INTO sales_daily (
  sales_date, channel, order_count, item_qty,
  gross_sales, discount_amount, net_sales
)
SELECT
  (current_date - (gs || ' days')::interval)::date as sales_date,
  'ALL',
  (50 + (gs % 200))::int,
  (120 + (gs % 500))::int,
  (500000 + (gs * 13000 % 2500000))::numeric(14,2),
  (20000 + (gs * 3000 % 250000))::numeric(14,2),
  ((500000 + (gs * 13000 % 2500000)) - (20000 + (gs * 3000 % 250000)))::numeric(14,2)
FROM generate_series(0, 364) gs;

-- 8) Automation jobs (20)
INSERT INTO automation_jobs (
  job_name, job_type, status, schedule_expr, payload,
  last_run_at, next_run_at, last_error
)
SELECT
  format('job-%02s', gs),
  (ARRAY['REPORT','SYNC','ALERT'])[((gs - 1) % 3) + 1],
  (ARRAY['PENDING','RUNNING','SUCCESS','FAILED'])[((gs - 1) % 4) + 1],
  '0 */2 * * *',
  jsonb_build_object('seed', true, 'jobNo', gs),
  now() - ((gs % 7) || ' hours')::interval,
  now() + ((gs % 7 + 1) || ' hours')::interval,
  CASE WHEN gs % 4 = 0 THEN 'seed error example' ELSE NULL END
FROM generate_series(1, 20) gs;

-- 9) AI query logs (500)
INSERT INTO ai_query_logs (
  user_id, question, answer, model,
  latency_ms, tokens_input, tokens_output, status, error_message
)
SELECT
  format('user-%03s', ((gs - 1) % 30) + 1),
  format('질문 샘플 %s: 오늘 재고 위험 알려줘', gs),
  CASE WHEN gs % 12 = 0 THEN NULL ELSE format('응답 샘플 %s', gs) END,
  'gpt-4o-mini',
  (200 + (gs % 1800))::int,
  (30 + (gs % 400))::int,
  (20 + (gs % 600))::int,
  CASE WHEN gs % 12 = 0 THEN 'FAILED' ELSE 'SUCCESS' END,
  CASE WHEN gs % 12 = 0 THEN 'seed timeout' ELSE NULL END
FROM generate_series(1, 500) gs;

COMMIT;

-- quick sanity counts
SELECT 'warehouses' AS tbl, count(*) FROM warehouses
UNION ALL SELECT 'products', count(*) FROM products
UNION ALL SELECT 'inventory_snapshots', count(*) FROM inventory_snapshots
UNION ALL SELECT 'stock_movements', count(*) FROM stock_movements
UNION ALL SELECT 'purchase_orders', count(*) FROM purchase_orders
UNION ALL SELECT 'purchase_order_items', count(*) FROM purchase_order_items
UNION ALL SELECT 'sales_daily', count(*) FROM sales_daily
UNION ALL SELECT 'automation_jobs', count(*) FROM automation_jobs
UNION ALL SELECT 'ai_query_logs', count(*) FROM ai_query_logs
ORDER BY tbl;
