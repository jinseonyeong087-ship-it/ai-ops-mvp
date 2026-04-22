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

## 프로젝트 구조
```bash
ai-ops-mvp/
├─ backend/
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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- health check: `GET /health`
- sample endpoint: `POST /api/ops/ask`

## 설계 문서 시작점
- `docs/INDEX.md` (문서 순서/수정 규칙)
