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

## 현재 구현 상태 (2026-04-22)
- [x] DB 마이그레이션(Alembic) 초기 세팅
- [x] 초기 스키마 생성 (업무 테이블 9개 + `alembic_version`)
- [x] 안전 시드 데이터 약 8천 건 입력 스크립트
- [x] `GET /api/kpi/summary` 구현
- [x] `POST /api/ops/ask` (mock)
- [ ] `GET /api/inventory/items`
- [ ] `POST /api/inventory/movements`
- [ ] 발주 API 세트 (`/api/purchase-orders/*`)

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

## API 엔드포인트
- `GET /health`
- `POST /api/ops/ask`
- `GET /api/kpi/summary`

## 설계 문서 시작점
- `docs/INDEX.md` (문서 순서/수정 규칙)
