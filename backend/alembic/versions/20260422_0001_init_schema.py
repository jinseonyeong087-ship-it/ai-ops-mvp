"""init schema

Revision ID: 20260422_0001
Revises:
Create Date: 2026-04-22
"""

from alembic import op

revision = "20260422_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id BIGSERIAL PRIMARY KEY,
            sku VARCHAR(64) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            unit VARCHAR(30) NOT NULL DEFAULT 'ea',
            safety_stock INTEGER NOT NULL DEFAULT 0,
            reorder_point INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

        CREATE TABLE IF NOT EXISTS warehouses (
            id BIGSERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(255),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS inventory_snapshots (
            id BIGSERIAL PRIMARY KEY,
            product_id BIGINT NOT NULL REFERENCES products(id),
            warehouse_id BIGINT NOT NULL REFERENCES warehouses(id),
            on_hand_qty INTEGER NOT NULL DEFAULT 0,
            reserved_qty INTEGER NOT NULL DEFAULT 0,
            available_qty INTEGER NOT NULL DEFAULT 0,
            snapshot_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_inventory_snapshots_product_warehouse UNIQUE (product_id, warehouse_id)
        );

        CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_available_qty ON inventory_snapshots(available_qty);

        CREATE TABLE IF NOT EXISTS stock_movements (
            id BIGSERIAL PRIMARY KEY,
            product_id BIGINT NOT NULL REFERENCES products(id),
            warehouse_id BIGINT NOT NULL REFERENCES warehouses(id),
            movement_type VARCHAR(30) NOT NULL,
            qty INTEGER NOT NULL,
            reference_type VARCHAR(30),
            reference_id VARCHAR(100),
            note TEXT,
            moved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_stock_movements_product_warehouse_moved_at ON stock_movements(product_id, warehouse_id, moved_at DESC);
        CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id);

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id BIGSERIAL PRIMARY KEY,
            po_number VARCHAR(50) UNIQUE NOT NULL,
            supplier_name VARCHAR(150) NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
            order_date DATE NOT NULL,
            expected_date DATE,
            warehouse_id BIGINT NOT NULL REFERENCES warehouses(id),
            total_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
            memo TEXT,
            created_by VARCHAR(100),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
        CREATE INDEX IF NOT EXISTS idx_purchase_orders_order_date ON purchase_orders(order_date DESC);

        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id BIGSERIAL PRIMARY KEY,
            purchase_order_id BIGINT NOT NULL REFERENCES purchase_orders(id),
            product_id BIGINT NOT NULL REFERENCES products(id),
            ordered_qty INTEGER NOT NULL,
            received_qty INTEGER NOT NULL DEFAULT 0,
            unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,
            line_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_po_items_po_product UNIQUE (purchase_order_id, product_id)
        );

        CREATE TABLE IF NOT EXISTS sales_daily (
            id BIGSERIAL PRIMARY KEY,
            sales_date DATE NOT NULL,
            channel VARCHAR(50) NOT NULL DEFAULT 'ALL',
            order_count INTEGER NOT NULL DEFAULT 0,
            item_qty INTEGER NOT NULL DEFAULT 0,
            gross_sales NUMERIC(14,2) NOT NULL DEFAULT 0,
            discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
            net_sales NUMERIC(14,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_sales_daily_date_channel UNIQUE (sales_date, channel)
        );

        CREATE TABLE IF NOT EXISTS automation_jobs (
            id BIGSERIAL PRIMARY KEY,
            job_name VARCHAR(120) NOT NULL,
            job_type VARCHAR(50) NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            schedule_expr VARCHAR(120),
            payload JSONB,
            last_run_at TIMESTAMPTZ,
            next_run_at TIMESTAMPTZ,
            last_error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_automation_jobs_status_next_run_at ON automation_jobs(status, next_run_at);
        CREATE INDEX IF NOT EXISTS idx_automation_jobs_job_type ON automation_jobs(job_type);

        CREATE TABLE IF NOT EXISTS ai_query_logs (
            id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(100),
            question TEXT NOT NULL,
            answer TEXT,
            model VARCHAR(100),
            latency_ms INTEGER,
            tokens_input INTEGER,
            tokens_output INTEGER,
            status VARCHAR(30) NOT NULL DEFAULT 'SUCCESS',
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_ai_query_logs_created_at ON ai_query_logs(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_ai_query_logs_status ON ai_query_logs(status);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS ai_query_logs;
        DROP TABLE IF EXISTS automation_jobs;
        DROP TABLE IF EXISTS sales_daily;
        DROP TABLE IF EXISTS purchase_order_items;
        DROP TABLE IF EXISTS purchase_orders;
        DROP TABLE IF EXISTS stock_movements;
        DROP TABLE IF EXISTS inventory_snapshots;
        DROP TABLE IF EXISTS warehouses;
        DROP TABLE IF EXISTS products;
        """
    )
