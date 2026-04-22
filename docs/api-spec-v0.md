# AI Ops MVP API 명세 (v0)

기준: FastAPI + PostgreSQL
Base URL: `/api`
Format: `application/json`

---

## 0) 공통

### 공통 응답 포맷

성공:
```json
{
  "data": {},
  "meta": {}
}
```

실패:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "invalid request",
    "details": []
  }
}
```

### 공통 에러 코드
- `VALIDATION_ERROR` (400)
- `NOT_FOUND` (404)
- `CONFLICT` (409)
- `INTERNAL_ERROR` (500)

---

## 1) KPI 요약 API

## `GET /api/kpi/summary`

대시보드 상단 KPI 카드용 요약 데이터 반환.

### Query Params
- `from` (optional, `YYYY-MM-DD`) : 조회 시작일
- `to` (optional, `YYYY-MM-DD`) : 조회 종료일
- `warehouse_id` (optional, number) : 특정 창고 필터

### Response 200
```json
{
  "data": {
    "inventory": {
      "total_sku": 1280,
      "total_on_hand_qty": 50231,
      "low_stock_sku": 37,
      "out_of_stock_sku": 5
    },
    "purchase": {
      "draft_count": 8,
      "submitted_count": 14,
      "partial_received_count": 3,
      "overdue_count": 2
    },
    "sales": {
      "gross_sales": 12340000,
      "net_sales": 11780000,
      "order_count": 421,
      "growth_rate_pct": 6.2
    },
    "logistics": {
      "inbound_qty": 1200,
      "outbound_qty": 930
    }
  },
  "meta": {
    "from": "2026-04-01",
    "to": "2026-04-22",
    "warehouse_id": null
  }
}
```

### 비고
- `low_stock_sku`: `available_qty <= reorder_point` 기준
- `out_of_stock_sku`: `available_qty <= 0` 기준
- `overdue_count`: `status in (SUBMITTED, PARTIAL_RECEIVED)` + `expected_date < today`

---

## 2) 재고 API

## `GET /api/inventory/items`

상품별 재고 목록 조회 (검색/필터/정렬/페이지네이션)

### Query Params
- `q` (optional, string): SKU/상품명 검색
- `category` (optional, string)
- `warehouse_id` (optional, number)
- `stock_status` (optional, string): `NORMAL|LOW|OUT`
- `sort` (optional, string): `name|available_qty|updated_at`
- `order` (optional, string): `asc|desc` (default: `desc`)
- `page` (optional, number, default: 1)
- `size` (optional, number, default: 20, max: 100)

### Response 200
```json
{
  "data": [
    {
      "product_id": 1,
      "sku": "SKU-1001",
      "name": "유기농 사과",
      "category": "과일",
      "warehouse_id": 1,
      "warehouse_name": "메인창고",
      "on_hand_qty": 120,
      "reserved_qty": 30,
      "available_qty": 90,
      "safety_stock": 50,
      "reorder_point": 80,
      "stock_status": "NORMAL",
      "updated_at": "2026-04-22T12:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "size": 20,
    "total": 1
  }
}
```

---

## `POST /api/inventory/movements`

입출고/조정 이벤트 등록.

### Request Body
```json
{
  "product_id": 1,
  "warehouse_id": 1,
  "movement_type": "INBOUND",
  "qty": 100,
  "reference_type": "PO",
  "reference_id": "PO-20260422-001",
  "note": "초도 입고"
}
```

### Validation
- `movement_type` in `INBOUND|OUTBOUND|ADJUSTMENT|RETURN`
- `qty > 0`
- `OUTBOUND`일 때 가용재고 부족 시 409

### Response 201
```json
{
  "data": {
    "movement_id": 553,
    "product_id": 1,
    "warehouse_id": 1,
    "movement_type": "INBOUND",
    "qty": 100,
    "moved_at": "2026-04-22T12:33:11Z"
  }
}
```

---

## `GET /api/inventory/movements`

재고 변동 이력 조회.

### Query Params
- `product_id` (optional, number)
- `warehouse_id` (optional, number)
- `movement_type` (optional, string)
- `from` / `to` (optional, date)
- `page`, `size`

### Response 200
```json
{
  "data": [
    {
      "id": 553,
      "product_id": 1,
      "warehouse_id": 1,
      "movement_type": "INBOUND",
      "qty": 100,
      "reference_type": "PO",
      "reference_id": "PO-20260422-001",
      "note": "초도 입고",
      "moved_at": "2026-04-22T12:33:11Z"
    }
  ],
  "meta": {
    "page": 1,
    "size": 20,
    "total": 1
  }
}
```

---

## 3) 발주 API

## `POST /api/purchase-orders`

발주 생성.

### Request Body
```json
{
  "supplier_name": "ABC Supplier",
  "order_date": "2026-04-22",
  "expected_date": "2026-04-25",
  "warehouse_id": 1,
  "memo": "긴급 발주",
  "items": [
    { "product_id": 1, "ordered_qty": 120, "unit_price": 3500 },
    { "product_id": 2, "ordered_qty": 50, "unit_price": 12000 }
  ]
}
```

### Response 201
```json
{
  "data": {
    "id": 101,
    "po_number": "PO-20260422-0101",
    "status": "DRAFT",
    "total_amount": 1020000,
    "created_at": "2026-04-22T12:40:12Z"
  }
}
```

---

## `GET /api/purchase-orders`

발주 목록 조회.

### Query Params
- `status` (optional): `DRAFT|SUBMITTED|PARTIAL_RECEIVED|RECEIVED|CANCELED`
- `supplier_name` (optional)
- `from` / `to` (optional): order_date 범위
- `page`, `size`

### Response 200
```json
{
  "data": [
    {
      "id": 101,
      "po_number": "PO-20260422-0101",
      "supplier_name": "ABC Supplier",
      "status": "SUBMITTED",
      "order_date": "2026-04-22",
      "expected_date": "2026-04-25",
      "total_amount": 1020000,
      "warehouse_id": 1
    }
  ],
  "meta": {
    "page": 1,
    "size": 20,
    "total": 1
  }
}
```

---

## `GET /api/purchase-orders/{po_id}`

발주 상세 조회.

### Response 200
```json
{
  "data": {
    "id": 101,
    "po_number": "PO-20260422-0101",
    "supplier_name": "ABC Supplier",
    "status": "SUBMITTED",
    "order_date": "2026-04-22",
    "expected_date": "2026-04-25",
    "warehouse_id": 1,
    "total_amount": 1020000,
    "items": [
      {
        "id": 1001,
        "product_id": 1,
        "ordered_qty": 120,
        "received_qty": 0,
        "unit_price": 3500,
        "line_amount": 420000
      }
    ]
  }
}
```

---

## `PATCH /api/purchase-orders/{po_id}/status`

발주 상태 변경.

### Request Body
```json
{
  "status": "SUBMITTED"
}
```

### 상태 전이 규칙 (MVP)
- `DRAFT -> SUBMITTED|CANCELED`
- `SUBMITTED -> PARTIAL_RECEIVED|RECEIVED|CANCELED`
- `PARTIAL_RECEIVED -> RECEIVED|CANCELED`
- `RECEIVED`, `CANCELED` 이후 변경 불가

### Response 200
```json
{
  "data": {
    "id": 101,
    "status": "SUBMITTED",
    "updated_at": "2026-04-22T12:50:00Z"
  }
}
```

---

## `POST /api/purchase-orders/{po_id}/receive`

발주 입고 처리 + 재고 반영.

### Request Body
```json
{
  "received_at": "2026-04-22T13:00:00Z",
  "items": [
    { "product_id": 1, "received_qty": 60 },
    { "product_id": 2, "received_qty": 50 }
  ],
  "note": "1차 입고"
}
```

### 처리 규칙
1. `purchase_order_items.received_qty` 누적 업데이트
2. 각 item별 `stock_movements`에 `INBOUND` 기록
3. `inventory_snapshots` 수량 업데이트
4. 발주 상태 자동 계산
   - 일부 입고: `PARTIAL_RECEIVED`
   - 전량 입고: `RECEIVED`

### Response 200
```json
{
  "data": {
    "po_id": 101,
    "status": "PARTIAL_RECEIVED",
    "received_items": 2,
    "received_total_qty": 110
  }
}
```

---

## 4) 구현 우선순위

1. `GET /api/kpi/summary`
2. `GET /api/inventory/items`
3. `POST /api/inventory/movements`
4. `POST /api/purchase-orders`
5. `GET /api/purchase-orders`, `GET /api/purchase-orders/{id}`
6. `POST /api/purchase-orders/{id}/receive`

---

문서 버전: `v0.1`
최종 수정: `2026-04-22`
