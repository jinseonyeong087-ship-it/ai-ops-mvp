# 05. Implementation Plan

## Phase 0 — 설계 고정 (완료 기준)
- [x] Charter
- [x] Scope
- [x] Domain rules
- [x] DB spec
- [x] API spec
- [x] UI/UX spec
- [x] Consistency check

## Phase 1 — 백엔드 기반
1. DB 연결/ORM/Alembic 세팅
2. `db-spec.md` 기준 초기 마이그레이션 생성
3. seed 데이터 작성(상품/창고/재고/발주/매출)
4. KPI/재고/발주 API 구현
5. `/api/ops/ask` + `ai_query_logs` 저장 강화

## Phase 2 — 프론트 대시보드
1. Next.js 프로젝트 초기화
2. Dashboard 화면(카드+테이블+위젯)
3. 재고 목록/필터/정렬/페이지네이션
4. 발주 목록/상세/입고 처리 UI
5. AI 질의 패널 연결

## Phase 3 — 운영 가능 상태
1. Docker Compose에 DB 포함
2. 환경변수 정리(`.env.example` 갱신)
3. 기본 에러 핸들링/입력 검증/로그
4. 최소 테스트(핵심 API)

## 즉시 실행 TODO (이번 주)
- Day1: Alembic + DB DDL + seed
- Day2: KPI/재고 API
- Day3: 발주 API + 입고 처리
- Day4: Next.js 초기 대시보드
- Day5: API 연동/QA/버그 수정

---
버전: v0.2 / 최종 수정: 2026-04-22
