# AI Ops MVP DB 테이블 명세서 (v0)

> 대상: PostgreSQL 16+
> 목적: 재고/발주/물류/매출 운영 + AI 질의/자동화 로그를 처리하는 MVP 스키마
> 원칙: **실사용 가능한 최소 구조**로 시작하고, 이후 확장

---

## 1) 설계 원칙

- 모든 업무 데이터는 `created_at`, `updated_at` 기본 포함
- 상태값은 문자열 enum 패턴 사용(초기 MVP는 DB enum보다 `CHECK` 또는 앱 레벨 검증 권장)
- 재고는 `stock_movements`(이력) 기반이 원칙, 조회 성능을 위해 `inventory_snapshots` 사용
- 매출은 원천 주문 시스템 연동 전까지 일 집계 테이블(`sales_daily`)로 시작
- AI 결과는 운영 감사/추적을 위해 `ai_query_logs`에 저장

---

## 2) 테이블 개요

1. `products` — 상품 마스터
2. `warehouses` — 창고/보관 위치
3. `inventory_snapshots` — 상품-창고별 현재 재고 스냅샷
4. `stock_movements` — 입고/출고/조정 이력
5. `purchase_orders` — 발주 헤더
6. `purchase_order_items` — 발주 라인
7. `sales_daily` — 일 매출 집계
8. `automation_jobs` — 자동화 워크플로우 실행 관리
9. `ai_query_logs` — AI 질의/응답 로그

---

## 3) 상세 명세

## 3.1 products

**설명**: 상품 기본 정보 및 재고 기준값

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 상품 ID |
| sku | VARCHAR(64) | UNIQUE, NOT NULL | 내부 SKU |
| name | VARCHAR(255) | NOT NULL | 상품명 |
| category | VARCHAR(100) | NULL | 카테고리 |
| unit | VARCHAR(30) | NOT NULL DEFAULT 'ea' | 단위(ea, box 등) |
| safety_stock | INTEGER | NOT NULL DEFAULT 0 | 안전재고 |
| reorder_point | INTEGER | NOT NULL DEFAULT 0 | 발주 기준 재고 |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | 사용 여부 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정시각 |

**인덱스 권장**
- `idx_products_name (name)`
- `idx_products_category (category)`

---

## 3.2 warehouses

**설명**: 재고를 관리하는 물리/가상 창고

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 창고 ID |
| code | VARCHAR(50) | UNIQUE, NOT NULL | 창고 코드 |
| name | VARCHAR(100) | NOT NULL | 창고명 |
| location | VARCHAR(255) | NULL | 위치 설명 |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | 사용 여부 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정시각 |

---

## 3.3 inventory_snapshots

**설명**: 상품-창고 기준 현재 재고 수량(빠른 조회용)

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 스냅샷 ID |
| product_id | BIGINT | FK -> products.id, NOT NULL | 상품 |
| warehouse_id | BIGINT | FK -> warehouses.id, NOT NULL | 창고 |
| on_hand_qty | INTEGER | NOT NULL DEFAULT 0 | 현재고 |
| reserved_qty | INTEGER | NOT NULL DEFAULT 0 | 예약재고 |
| available_qty | INTEGER | NOT NULL DEFAULT 0 | 가용재고 (= on_hand - reserved) |
| snapshot_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 기준시각 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정시각 |

**유니크 제약**
- `(product_id, warehouse_id)`

**인덱스 권장**
- `idx_inventory_snapshots_available_qty (available_qty)`

---

## 3.4 stock_movements

**설명**: 재고 변동 원장(입고/출고/조정/반품 등)

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 변동 ID |
| product_id | BIGINT | FK -> products.id, NOT NULL | 상품 |
| warehouse_id | BIGINT | FK -> warehouses.id, NOT NULL | 창고 |
| movement_type | VARCHAR(30) | NOT NULL | `INBOUND`/`OUTBOUND`/`ADJUSTMENT`/`RETURN` |
| qty | INTEGER | NOT NULL | 변동 수량(양수 기준, 타입으로 방향 구분) |
| reference_type | VARCHAR(30) | NULL | `PO`/`SALE`/`MANUAL` 등 |
| reference_id | VARCHAR(100) | NULL | 외부 문서/연결 ID |
| note | TEXT | NULL | 메모 |
| moved_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 변동시각 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |

**인덱스 권장**
- `idx_stock_movements_product_warehouse_moved_at (product_id, warehouse_id, moved_at DESC)`
- `idx_stock_movements_reference (reference_type, reference_id)`

---

## 3.5 purchase_orders

**설명**: 발주 헤더

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 발주 ID |
| po_number | VARCHAR(50) | UNIQUE, NOT NULL | 발주번호 |
| supplier_name | VARCHAR(150) | NOT NULL | 공급사명 |
| status | VARCHAR(30) | NOT NULL DEFAULT 'DRAFT' | `DRAFT`/`SUBMITTED`/`PARTIAL_RECEIVED`/`RECEIVED`/`CANCELED` |
| order_date | DATE | NOT NULL | 발주일 |
| expected_date | DATE | NULL | 입고예정일 |
| warehouse_id | BIGINT | FK -> warehouses.id, NOT NULL | 입고 창고 |
| total_amount | NUMERIC(14,2) | NOT NULL DEFAULT 0 | 총액 |
| memo | TEXT | NULL | 메모 |
| created_by | VARCHAR(100) | NULL | 작성자 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정시각 |

**인덱스 권장**
- `idx_purchase_orders_status (status)`
- `idx_purchase_orders_order_date (order_date DESC)`

---

## 3.6 purchase_order_items

**설명**: 발주 상세 라인

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 라인 ID |
| purchase_order_id | BIGINT | FK -> purchase_orders.id, NOT NULL | 발주 헤더 |
| product_id | BIGINT | FK -> products.id, NOT NULL | 상품 |
| ordered_qty | INTEGER | NOT NULL | 발주수량 |
| received_qty | INTEGER | NOT NULL DEFAULT 0 | 입고수량 |
| unit_price | NUMERIC(12,2) | NOT NULL DEFAULT 0 | 단가 |
| line_amount | NUMERIC(14,2) | NOT NULL DEFAULT 0 | 금액 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정시각 |

**유니크 제약(권장)**
- `(purchase_order_id, product_id)`

---

## 3.7 sales_daily

**설명**: 일 단위 매출/주문 집계(MVP)

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 집계 ID |
| sales_date | DATE | NOT NULL | 기준일 |
| channel | VARCHAR(50) | NOT NULL DEFAULT 'ALL' | 판매 채널 |
| order_count | INTEGER | NOT NULL DEFAULT 0 | 주문수 |
| item_qty | INTEGER | NOT NULL DEFAULT 0 | 판매수량 |
| gross_sales | NUMERIC(14,2) | NOT NULL DEFAULT 0 | 총매출 |
| discount_amount | NUMERIC(14,2) | NOT NULL DEFAULT 0 | 할인 |
| net_sales | NUMERIC(14,2) | NOT NULL DEFAULT 0 | 순매출 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정시각 |

**유니크 제약**
- `(sales_date, channel)`

---

## 3.8 automation_jobs

**설명**: 반복 업무 자동화 실행/이력 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 작업 ID |
| job_name | VARCHAR(120) | NOT NULL | 작업명 |
| job_type | VARCHAR(50) | NOT NULL | `REPORT`/`SYNC`/`ALERT` 등 |
| status | VARCHAR(30) | NOT NULL DEFAULT 'PENDING' | `PENDING`/`RUNNING`/`SUCCESS`/`FAILED` |
| schedule_expr | VARCHAR(120) | NULL | cron/주기 표현식 |
| payload | JSONB | NULL | 실행 파라미터 |
| last_run_at | TIMESTAMPTZ | NULL | 마지막 실행 시각 |
| next_run_at | TIMESTAMPTZ | NULL | 다음 실행 시각 |
| last_error | TEXT | NULL | 실패 메시지 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정시각 |

**인덱스 권장**
- `idx_automation_jobs_status_next_run_at (status, next_run_at)`
- `idx_automation_jobs_job_type (job_type)`

---

## 3.9 ai_query_logs

**설명**: AI 질의/응답/성능 추적 및 감사 로그

| 컬럼명 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 로그 ID |
| user_id | VARCHAR(100) | NULL | 사용자 식별자 |
| question | TEXT | NOT NULL | 사용자 질문 |
| answer | TEXT | NULL | AI 응답 |
| model | VARCHAR(100) | NULL | 사용 모델 |
| latency_ms | INTEGER | NULL | 응답시간 |
| tokens_input | INTEGER | NULL | 입력 토큰 |
| tokens_output | INTEGER | NULL | 출력 토큰 |
| status | VARCHAR(30) | NOT NULL DEFAULT 'SUCCESS' | `SUCCESS`/`FAILED` |
| error_message | TEXT | NULL | 오류 내용 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성시각 |

**인덱스 권장**
- `idx_ai_query_logs_created_at (created_at DESC)`
- `idx_ai_query_logs_status (status)`

---

## 4) 관계 요약 (ERD 텍스트)

- `products` 1 --- N `inventory_snapshots`
- `warehouses` 1 --- N `inventory_snapshots`
- `products` 1 --- N `stock_movements`
- `warehouses` 1 --- N `stock_movements`
- `purchase_orders` 1 --- N `purchase_order_items`
- `products` 1 --- N `purchase_order_items`
- `warehouses` 1 --- N `purchase_orders`

---

## 5) 상태값(코드) 표준

- `purchase_orders.status`
  - `DRAFT`, `SUBMITTED`, `PARTIAL_RECEIVED`, `RECEIVED`, `CANCELED`
- `stock_movements.movement_type`
  - `INBOUND`, `OUTBOUND`, `ADJUSTMENT`, `RETURN`
- `automation_jobs.status`
  - `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`
- `ai_query_logs.status`
  - `SUCCESS`, `FAILED`

---

## 6) MVP API와의 1차 매핑

- `/health` → 시스템 상태
- `/api/ops/ask` → `ai_query_logs`
- (추가 예정) `/api/kpi/summary` → `inventory_snapshots`, `sales_daily`, `purchase_orders`
- (추가 예정) `/api/inventory/*` → `products`, `inventory_snapshots`, `stock_movements`
- (추가 예정) `/api/purchase-orders/*` → `purchase_orders`, `purchase_order_items`

---

## 7) 다음 단계 체크리스트

1. Alembic 초기 마이그레이션 생성
2. 위 9개 테이블 DDL 반영
3. 샘플 데이터 시드 작성(상품/재고/발주/매출)
4. KPI API 1차 구현
5. 대시보드 테이블/카드 화면 연동

---

## 8) 확장 후보 (v1+)

- `suppliers` (공급사 마스터 분리)
- `sales_orders`/`sales_order_items` (원천 주문 단위)
- `users`/`roles`/`audit_logs` (권한 및 감사)
- `notifications` (알림 정책)
- `workflow_rules` (조건/액션 자동화 룰 엔진)

---

문서 버전: `v0.1`  
최종 수정: `2026-04-22`
