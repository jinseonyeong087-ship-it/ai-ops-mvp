# 06. Consistency Check (문서 정합성 검증)

검증일: 2026-04-22  
기준 문서: `00-charter.md`, `01-mvp-scope.md`, `02-domain-rules.md`, `db-spec.md`, `api-spec-v0.md`, `04-ui-ux-spec.md`, `05-implementation-plan.md`

---

## 1) 범위 정합성

- Scope의 In-Scope 기능(재고/발주/KPI/AI 질의)은 API 명세에 모두 존재 ✅
- API 명세의 핵심 엔드포인트는 UI/UX 화면 매핑에 모두 존재 ✅
- DB 테이블 9개는 Scope 기능을 커버함 ✅

---

## 2) 상태값 정합성

| 대상 | 상태값 | 문서 일치 |
|---|---|---|
| 발주 상태 | DRAFT, SUBMITTED, PARTIAL_RECEIVED, RECEIVED, CANCELED | ✅ (`db-spec.md`, `api-spec-v0.md`, `02-domain-rules.md`) |
| 재고 이동 타입 | INBOUND, OUTBOUND, ADJUSTMENT, RETURN | ✅ |
| AI 로그 상태 | SUCCESS, FAILED | ✅ |

---

## 3) KPI 규칙 정합성

- LOW/OUT 분류 기준: `02-domain-rules.md`와 `api-spec-v0.md` 일치 ✅
- 발주 지연 기준(`expected_date < today` + 미종결): 일치 ✅

---

## 4) 누락/충돌 점검

### 확인된 이슈
1. 루트 `README.md`의 docs 구조가 구버전 표기(`roadmap.md`만 표시)
2. `docs/roadmap.md`가 최신 설계 문서 체계를 반영하지 않음

### 조치
- README와 roadmap을 최신 설계 문서 체계 기준으로 갱신 필요

---

## 5) 최종 판정

- 핵심 설계 문서 간 기능/데이터/상태값 충돌 없음
- 구현 착수 가능 상태
- 단, README/roadmap 최신화 후 문서 일관성 100% 달성

---
버전: v0.2 / 최종 수정: 2026-04-22
