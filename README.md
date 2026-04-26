# AI Ops MVP

사내 운영 효율화를 위한 AI 기반 업무 시스템 MVP입니다.

## 목표
- 반복 업무 자동화
- 운영 데이터(재고/발주/매출) 가시화
- 리포트 자동 생성
- AI 질의 기반 업무 지원

## 권장 스택
- Frontend: Next.js (dashboard)
- Backend: FastAPI
- DB: PostgreSQL
- Queue(optional): Redis + worker

## MVP 기능 (1차)
1. 자동화 요청 등록/관리
2. KPI 대시보드(재고/발주/매출)
3. AI 업무 질의 API (요약/분석)
4. 일간 리포트 자동 생성

## 현재 구현 상태 (2026-04-23)

### 완료
- [x] DB 마이그레이션(Alembic) 초기 세팅
- [x] 초기 스키마 생성 (업무 테이블 9개 + `alembic_version`)
- [x] 안전 시드 데이터 약 8천 건 입력 스크립트
- [x] `POST /api/ops/ask` (mock)
- [x] `GET /api/kpi/summary` 구현
- [x] 재고/발주 핵심 API 코드 한국어 주석 보강 (유지보수성 개선)
- [x] 스모크 테스트 재검증 (`make smoke` PASS)

### 다음 구현 순서 (우선순위)
- [x] 1. `GET /api/inventory/items` (검색/필터/정렬/페이지네이션)
- [x] 2. `POST /api/inventory/movements` (입출고/조정 등록 + 유효성 검증)
- [x] 3. `GET /api/inventory/movements` (이력 조회)
- [x] 4. `POST /api/purchase-orders` (발주 생성)
- [x] 5. `GET /api/purchase-orders` (발주 목록)
- [x] 6. `GET /api/purchase-orders/{po_id}` (발주 상세)
- [x] 7. `PATCH /api/purchase-orders/{po_id}/status` (상태 변경)
- [x] 8. `POST /api/purchase-orders/{po_id}/receive` (입고 처리 + 재고 반영)

### 인프라/운영 (MVP 필수)
- [x] 9. `docker-compose`에 PostgreSQL 서비스 추가 및 환경변수 연동
- [x] 10. 백엔드 컨테이너 실행/마이그레이션 명령 정리
- [x] 11. `.env.example`와 실제 실행 스크립트 동기화
- [x] 12. 기본 에러 핸들링 및 입력 검증 표준화
- [x] 13. 핵심 API 스모크 테스트 추가

### 프론트엔드 (대시보드)
- [x] 14. Next.js 초기 프로젝트 구성
- [x] 15. KPI 카드 + 재고 테이블 + 위험 위젯 화면 구현
- [x] 16. 발주 목록/상세/입고 처리 UI 구현
- [x] 17. AI 질의 패널 연결 (`POST /api/ops/ask`)

### 배포 준비
- [x] 18. 운영용 환경변수/비밀값 관리 방식 확정 (`.env.example` + `scripts/validate_env.sh` + compose 필수값 검증)
- [ ] 19. 배포 절차 문서화(수동 배포 기준)
- [ ] 20. CI/CD 최소 파이프라인(테스트/빌드) 구성

## 프로젝트 구조
```bash
ai-ops-mvp/
├─ backend/
│  ├─ alembic.ini
│  ├─ alembic/
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions/
│  │     └─ 20260422_0001_init_schema.py
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ api/
│  │  │  ├─ health.py
│  │  │  ├─ ops.py
│  │  │  └─ kpi.py
│  │  ├─ models/
│  │  │  └─ schemas.py
│  │  └─ services/
│  │     └─ ai_service.py
│  ├─ scripts/
│  │  └─ seed_safe_8k.sql
│  └─ requirements.txt
├─ frontend/
├─ infra/
├─ docs/
│  ├─ INDEX.md
│  ├─ 00-charter.md
│  ├─ 01-mvp-scope.md
│  ├─ 02-domain-rules.md
│  ├─ db-spec.md
│  ├─ api-spec-v0.md
│  ├─ 04-ui-ux-spec.md
│  ├─ 05-implementation-plan.md
│  ├─ 06-consistency-check.md
│  └─ roadmap.md
├─ .env.example
├─ Makefile
└─ .gitignore
```

## 빠른 시작 (backend)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# WSL 로컬 PostgreSQL 기준
export DATABASE_URL='postgresql+psycopg://<DB_USER>:<DB_PASSWORD>@localhost:5432/ai_ops_mvp_dev'

# DB 스키마 반영
alembic upgrade head

# 시드 데이터 입력(선택)
PGPASSWORD='<DB_PASSWORD>' psql -h localhost -U <DB_USER> -d ai_ops_mvp_dev -f scripts/seed_safe_8k.sql

# API 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker 실행/마이그레이션 명령 (권장)
```bash
# 프로젝트 루트에서 실행
make init-env

# 환경변수 검증 (개발)
make validate-env

# 환경변수 검증 (운영 기준 placeholder/빈값 차단)
make validate-env-prod

# 컨테이너 기동 (postgres + backend)
make up

# DB 마이그레이션 적용
make migrate

# 시드 입력(선택)
make seed

# 핵심 API 스모크 테스트
make smoke

# 상태/로그 확인
make ps
make logs

# 종료
make down
```

직접 실행이 필요하면 아래 명령도 동일합니다.
```bash
docker compose -f infra/docker-compose.yml --env-file .env up -d
docker compose -f infra/docker-compose.yml --env-file .env exec backend alembic upgrade head
```

## API 엔드포인트
- `GET /health`
- `POST /api/ops/ask`
- `GET /api/kpi/summary`

## 설계 문서 시작점
- `docs/INDEX.md` (문서 순서/수정 규칙)
