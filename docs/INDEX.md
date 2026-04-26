# AI Ops MVP 문서 인덱스 (Single Source of Truth)

이 폴더 문서들은 **초기 설계 결정사항**을 고정하기 위한 기준 문서입니다.
구현 전에 아래 순서대로 합의하고 진행합니다.

---

## 1) 필수 합의 문서

1. `00-charter.md`  
   - 왜 만드는지, 누구를 위한지, 성공 기준
2. `01-mvp-scope.md`  
   - MVP 범위 / 제외 범위 / 우선순위
3. `02-domain-rules.md`  
   - 운영 규칙(재고, 발주, 입고, KPI 계산 기준)
4. `db-spec.md`  
   - 데이터 모델(테이블, 컬럼, 관계)
5. `api-spec-v0.md`  
   - API 계약(요청/응답/검증/상태 전이)
6. `04-ui-ux-spec.md`  
   - UI 정보구조/화면 블록/가독성 규칙
7. `05-implementation-plan.md`  
   - 실제 구현 순서(백엔드/프론트/인프라)
8. `06-consistency-check.md`  
   - 문서 간 정합성 검증 결과
9. `07-env-secret-policy.md`
   - 환경변수/비밀값 관리 원칙과 운영 검증 기준
10. `08-manual-deploy-runbook.md`
   - 수동 배포/검증/롤백 절차 표준
11. `09-ci-cd-minimum.md`
   - 최소 CI 파이프라인과 품질 게이트
9. `07-env-secrets.md`
   - 환경변수/비밀값 관리 기준(개발/운영 공통)

---

## 2) 수정 규칙

- DB 필드/상태값 변경 시: `db-spec.md` + `api-spec-v0.md` + `06-consistency-check.md` 동시 갱신
- 화면 KPI 변경 시: `02-domain-rules.md` + `04-ui-ux-spec.md` + `api-spec-v0.md` 동시 갱신
- MVP 범위 변경 시: `01-mvp-scope.md` + `05-implementation-plan.md` 동시 갱신

---

## 3) 현재 버전

- 기준 버전: `v0.2`
- 기준일: `2026-04-22`
