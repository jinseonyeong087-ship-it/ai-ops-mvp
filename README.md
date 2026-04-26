# AI Ops MVP

Docker 기반으로 실행되는 **사내 운영관리 웹 애플리케이션**입니다.  
재고/발주/판매 데이터를 한 화면에서 관리하고, 운영자가 빠르게 의사결정할 수 있도록 KPI/위험지표/업무 입력 UI를 제공합니다.

실행 환경 기준:
- Local: Docker Compose
- CI: GitHub Actions
- Backend: FastAPI
- Frontend: Next.js
- DB: PostgreSQL

---

## 서비스 소개

이 서비스는 운영팀의 반복 업무를 줄이고, 데이터 기반으로 상태를 점검할 수 있게 만드는 웹입니다.

주요 기능:
- 대시보드 KPI (재고/매출/발주 지연)
- 재고 리스트 및 위험 위젯(품절/품절 임박)
- 발주 목록/상세/입고 처리
- 상품 등록
- 스케줄 등록/조회
- 판매현황 등록/조회
- AI 질의 패널 (`POST /api/ops/ask`)

---

## Components

- Frontend (`frontend/src/app`)
  - Next.js App Router 기반 운영 UI
- Frontend API client (`frontend/src/lib/api.ts`)
  - Backend API 호출/응답 타입 관리
- Backend API (`backend/app/main.py`, `backend/app/api/*`)
  - KPI/재고/발주/운영 API 제공
- DB Migration (`backend/alembic`, `backend/alembic.ini`)
  - 스키마 버전 관리
- Infra (`infra/docker-compose.yml`)
  - postgres + backend 컨테이너 실행
- CI (`.github/workflows/ci.yml`)
  - backend smoke + frontend lint/build 검증

---

## System Flow

```mermaid
flowchart LR
A[운영 사용자] -->|브라우저 접속| B[Next.js Frontend]
B -->|REST API| C[FastAPI Backend]
C -->|SQL| D[(PostgreSQL)]
B -->|AI 질의| C

E[GitHub Push/PR] --> F[GitHub Actions CI]
F -->|backend smoke| C
F -->|frontend lint/build| B
```

---

## Sequence Diagram

```mermaid
sequenceDiagram
autonumber
participant U as User
participant FE as Frontend
participant BE as Backend API
participant DB as PostgreSQL

U->>FE: 대시보드 접속
FE->>BE: GET /api/kpi/summary
BE->>DB: KPI 집계 쿼리
DB-->>BE: 집계 결과
BE-->>FE: KPI JSON
FE-->>U: 카드/테이블/위험 위젯 렌더링

U->>FE: 발주 입고 처리
FE->>BE: POST /api/purchase-orders/{id}/receive
BE->>DB: 발주/재고 트랜잭션 반영
DB-->>BE: 처리 성공
BE-->>FE: 결과 응답
FE-->>U: 상태 업데이트
```

---

## 실제 UI 화면

### 1) Dashboard
![대시보드 화면](docs/images/ui-dashboard.png)

### 2) Purchase Orders
![발주 목록 화면](docs/images/ui-purchase-orders.png)

### 3) Sales
![판매 현황 화면](docs/images/ui-sales.png)

---

## Security Check (전체 서비스 기준 점검 결과)

점검일: 2026-04-26

### 1) Secret/환경변수 관리
- `.env`, `.env.*` git ignore 적용
- `.env.example` 템플릿 분리
- 운영 배포 전 검증 스크립트 적용: `scripts/validate_env.sh`
- `make validate-env-prod`에서 placeholder 차단
- compose 필수값 강제: `POSTGRES_PASSWORD`, `DATABASE_URL`

### 2) 자동 검증/품질 게이트
- CI 파이프라인 적용: `.github/workflows/ci.yml`
  - backend smoke
  - frontend lint/build

### 3) 취약점 스캔 결과
- Python (`pip-audit`) 점검 수행
  - `python-dotenv` 취약점 대응 완료: `1.0.1 -> 1.2.2`
  - `fastapi` 상향: `0.115.0 -> 0.116.1`
  - 잔여 이슈: `starlette` 1건 (FastAPI 의존성 상한으로 즉시 상향 불가)
- Node (`npm audit --omit=dev`) 점검 수행
  - `postcss` 관련 moderate 경고 표시됨(Next 트리 경유)

### 4) 보안 권고(다음 단계)
- Reverse proxy/nginx 레이어에서 업로드 크기 제한
- WAF/Rate Limit 적용
- SAST + dependency scan(주간) 자동화
- 운영 키 정기 회전 및 권한 최소화

---

## Runtime and Operations

### 환경변수 예시
```env
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
POSTGRES_DB=ai_ops_mvp_dev
POSTGRES_USER=aiops
POSTGRES_PASSWORD=__REPLACE_WITH_STRONG_PASSWORD__
DATABASE_URL=postgresql+psycopg://aiops:__REPLACE_WITH_STRONG_PASSWORD__@postgres:5432/ai_ops_mvp_dev
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
AI_API_KEY=__SET_LOCALLY__
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

### Docker 실행
```bash
make init-env
make validate-env
make up
make migrate
make seed
make smoke
```

### 운영 배포 전 검증
```bash
make validate-env-prod ENV_FILE=.env
```

---

## API Endpoints (핵심)
- `GET /health`
- `POST /api/ops/ask`
- `GET /api/kpi/summary`
- `GET /api/inventory/items`
- `GET /api/purchase-orders`
- `POST /api/purchase-orders/{po_id}/receive`
- `GET /api/sales/daily`
- `POST /api/sales/daily`

---

## Key Files
- `frontend/src/app/page.tsx`
- `frontend/src/app/components/app-shell.tsx`
- `frontend/src/lib/api.ts`
- `backend/app/main.py`
- `backend/app/api/kpi.py`
- `backend/app/api/purchase_orders.py`
- `infra/docker-compose.yml`
- `.github/workflows/ci.yml`
- `docs/08-manual-deploy-runbook.md`
- `docs/09-ci-cd-minimum.md`

---

## 문서 시작점
- `docs/INDEX.md`
