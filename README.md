# AI Ops MVP

사내 운영 효율화를 위한 AI 기반 업무 시스템 MVP입니다.

## 이 웹이 하는 일
이 프로젝트는 **사내 운영팀을 위한 웹 대시보드**입니다.
재고/발주/판매 데이터를 한 화면에서 보고, 필요한 운영 액션(입고 처리, 상품 등록, 스케줄 등록 등)을 바로 실행할 수 있게 만든 AI Ops MVP입니다.

## 어떤 사용자에게 필요한가
- 재고 부족/품절 위험을 빠르게 파악해야 하는 운영 담당자
- 발주 상태와 입고 진행을 매일 점검하는 구매/물류 담당자
- 일일 매출과 채널별 흐름을 확인하는 관리자

## 핵심 기능
- **대시보드:** KPI 요약, 재고 리스트, 재고 위험 위젯
- **발주 관리:** 발주 목록/상세 조회, 입고 처리
- **상품 관리:** 신규 상품 등록
- **스케줄 관리:** 운영 작업 스케줄 등록/조회
- **판매 현황:** 일별 판매 데이터 등록/조회
- **AI 질의 패널:** 운영 데이터에 대한 질의 응답 (`/api/ops/ask`)

## 기술 구성
- Frontend: Next.js
- Backend: FastAPI
- DB: PostgreSQL
- 배포/운영: Docker Compose + Makefile
- CI: GitHub Actions (백엔드 스모크 + 프론트 lint/build)

## 현재 상태 요약
- MVP 핵심 기능 구현 완료
- 운영 환경변수/비밀값 관리 정책 확정
- 수동 배포 런북 문서화 완료
- 최소 CI/CD 파이프라인 구성 완료

## 서비스 소개
AI Ops MVP는 운영팀이 매일 반복하는 재고/발주/판매 점검 업무를 한 곳에서 처리할 수 있도록 만든 **운영 대시보드 웹 서비스**입니다.

이 웹에서 할 수 있는 핵심 작업:
- 현재 재고와 품절 위험 SKU를 즉시 확인
- 발주 상태를 조회하고 입고를 반영
- 상품 신규 등록
- 운영 스케줄 등록 및 조회
- 일별 판매 데이터 입력/확인
- 운영 질의를 AI 패널로 빠르게 확인

## 실제 UI 화면
### 1) 대시보드
![대시보드 화면](docs/images/ui-dashboard.png)

### 2) 발주 목록
![발주 목록 화면](docs/images/ui-purchase-orders.png)

### 3) 판매 현황
![판매 현황 화면](docs/images/ui-sales.png)

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
