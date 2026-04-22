# 01. MVP Scope

## 1) In Scope (이번에 반드시)

### A. 재고
- 상품/창고 기준 재고 조회
- 가용재고 기준 `NORMAL/LOW/OUT` 상태 분류
- 입출고/조정 이력 기록

### B. 발주
- 발주 생성
- 발주 목록/상세 조회
- 상태 변경 (`DRAFT/SUBMITTED/PARTIAL_RECEIVED/RECEIVED/CANCELED`)
- 입고 처리 시 재고 자동 반영

### C. KPI 대시보드
- 재고 요약: 총 SKU, 총재고, 품절임박, 품절
- 발주 요약: 상태별 건수, 지연 건수
- 매출 요약: gross/net/order_count
- 물류 요약: 입고/출고 수량

### D. AI 업무 질의
- `/api/ops/ask` 기본 제공
- 질의/응답 로그 저장 (`ai_query_logs`)

---

## 2) Out of Scope (다음 단계)
- 공급사 마스터 분리(`suppliers`)
- 원천 주문 단위(`sales_orders`) 상세 관리
- 고급 권한/감사 로그 완성형
- 룰 기반 자동화 엔진 UI

---

## 3) 우선순위
1. KPI 조회 API
2. 재고 목록 API
3. 재고 변동 등록 API
4. 발주 생성/조회 API
5. 입고 처리 API
6. 프론트 대시보드 연동

---

## 4) 수용 기준 (Acceptance)
- 재고 테이블에서 필터/검색/정렬이 동작
- 발주 생성 후 입고 처리 시 재고가 증가
- KPI 수치가 DB 기반으로 계산되어 반환
- API 명세와 응답 필드가 일치

---
버전: v0.2 / 최종 수정: 2026-04-22
