# 02. Domain Rules (운영 규칙)

## 1) 재고 규칙

- `available_qty = on_hand_qty - reserved_qty`
- 재고 상태 분류
  - `OUT`: `available_qty <= 0`
  - `LOW`: `available_qty > 0 AND available_qty <= reorder_point`
  - `NORMAL`: 그 외
- 출고(`OUTBOUND`) 등록 시 `available_qty` 부족이면 거절(409)

## 2) 재고 반영 규칙

- 모든 입출고 이벤트는 `stock_movements`에 기록
- `inventory_snapshots`는 조회 최적화용 집계 상태
- 입고/출고/조정 이벤트 발생 시 snapshot 갱신

## 3) 발주 상태 전이

- `DRAFT -> SUBMITTED|CANCELED`
- `SUBMITTED -> PARTIAL_RECEIVED|RECEIVED|CANCELED`
- `PARTIAL_RECEIVED -> RECEIVED|CANCELED`
- `RECEIVED|CANCELED`는 종료 상태(변경 불가)

## 4) 입고 처리 규칙

발주 입고 처리 시:
1. `purchase_order_items.received_qty` 누적
2. `stock_movements`에 `INBOUND` 기록
3. `inventory_snapshots.on_hand_qty` 증가
4. 발주 상태 자동 재계산

## 5) KPI 계산 규칙

- 재고 KPI
  - `total_sku`: 활성 상품 수
  - `total_on_hand_qty`: snapshot 합계
  - `low_stock_sku`: LOW 상태 SKU 수
  - `out_of_stock_sku`: OUT 상태 SKU 수
- 발주 KPI
  - 상태별 건수 + 지연건수(`expected_date < today` and 상태 미종결)
- 매출 KPI
  - `sales_daily` 합산(gross/net/order_count)
- 물류 KPI
  - 기간 내 `stock_movements`의 INBOUND/OUTBOUND qty 합

## 6) AI 질의 로그 규칙

- `/api/ops/ask` 호출 시 요청/응답/지연시간/상태를 `ai_query_logs`에 기록
- 실패도 반드시 기록(`status=FAILED`, `error_message`)

---
버전: v0.2 / 최종 수정: 2026-04-22
