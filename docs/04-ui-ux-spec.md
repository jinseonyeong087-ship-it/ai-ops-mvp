# 04. UI/UX Spec (가독성 중심 대시보드)

## 1) UX 목표
- 운영 담당자가 3분 내 핵심 상태를 파악
- 재고 위험 항목을 즉시 식별
- 발주 생성/입고 반영 동선을 짧게 유지

## 2) 정보 구조 (IA)

### 좌측 사이드바
- Dashboard
- 재고 관리
- 발주 관리
- 입출고 이력
- 리포트
- 설정

### 상단 바
- 검색(상품/SKU/발주번호)
- 사용자 메뉴

### 메인 영역
1. KPI 카드 4~6개
2. 재고 테이블(검색/필터/정렬)
3. 품절 임박/품절 위젯
4. 최근 발주/입고 상태 위젯
5. AI 질의 패널(우측 또는 하단)

## 3) 핵심 컴포넌트
- KPI 카드
- 상태 배지 (`NORMAL|LOW|OUT`, `DRAFT|SUBMITTED|...`)
- 필터 바(기간/카테고리/창고/상태)
- 데이터 테이블(페이지네이션)
- 빠른 액션 버튼(상품 등록/발주 생성/내보내기)
- AI 질문 입력 + 응답 카드

## 4) 가독성 원칙
- 테이블 중심 레이아웃 우선
- 색상은 상태 전달에만 사용(과도한 장식 금지)
- 숫자는 천 단위 구분 + 우측 정렬
- 필터/정렬/페이지네이션 위치 고정

## 5) 화면-API 매핑
- Dashboard: `GET /api/kpi/summary`
- 재고 목록: `GET /api/inventory/items`
- 입출고 등록: `POST /api/inventory/movements`
- 발주 목록/상세: `GET /api/purchase-orders`, `GET /api/purchase-orders/{id}`
- 발주 생성: `POST /api/purchase-orders`
- 입고 처리: `POST /api/purchase-orders/{id}/receive`
- AI 패널: `POST /api/ops/ask`

---
버전: v0.2 / 최종 수정: 2026-04-22
