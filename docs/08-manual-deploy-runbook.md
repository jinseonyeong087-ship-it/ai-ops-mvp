# 08-manual-deploy-runbook.md

## 목적
MVP 단계에서 사람이 따라할 수 있는 **수동 배포 표준 절차**를 정의한다.

---

## 0) 배포 원칙
- 운영 배포는 `main` 최신 커밋 기준으로 수행한다.
- 배포 전 반드시 환경변수 검증을 통과해야 한다.
- 배포 후 스모크 테스트에 실패하면 즉시 롤백한다.
- 비밀값은 저장소가 아닌 서버 환경파일로만 관리한다.

---

## 1) 사전 준비 (서버 1회)
1. 서버에 Docker / Docker Compose 설치
2. 앱 디렉터리 준비 (예: `/opt/ai-ops-mvp`)
3. 저장소 클론
4. `.env` 생성 (`.env.example` 기반)
5. 운영값으로 교체
   - `POSTGRES_PASSWORD`
   - `DATABASE_URL`
   - `AI_API_KEY`
   - `APP_ENV=production`

---

## 2) 배포 절차 (매 릴리즈)
아래 명령은 프로젝트 루트 기준.

```bash
# 1) 최신 코드 반영
git fetch origin
git checkout main
git pull --ff-only origin main

# 2) 운영 환경변수 검증
make validate-env-prod ENV_FILE=.env

# 3) 컨테이너 재기동(최신 코드 반영)
make down ENV_FILE=.env
make up ENV_FILE=.env

# 4) 마이그레이션 적용
make migrate ENV_FILE=.env

# 5) 상태/로그 확인
make ps ENV_FILE=.env
make logs ENV_FILE=.env

# 6) 스모크 테스트
make smoke
```

---

## 3) 배포 검증 체크리스트
- [ ] `make validate-env-prod` 통과
- [ ] `make ps`에서 postgres/backend 모두 healthy/Up
- [ ] `GET /health` 200 응답
- [ ] 핵심 API 스모크 테스트 통과 (`make smoke`)
- [ ] 프론트 주요 화면 수동 확인 (대시보드/발주/판매/스케줄)

---

## 4) 롤백 절차
문제 발생 시 직전 정상 커밋으로 복구한다.

```bash
# 1) 직전 정상 커밋으로 이동
git log --oneline -n 10
git checkout <LAST_GOOD_COMMIT>

# 2) 컨테이너 재기동 + 마이그레이션 확인
make down ENV_FILE=.env
make up ENV_FILE=.env
make migrate ENV_FILE=.env

# 3) 스모크 테스트로 복구 확인
make smoke
```

> 주의: 스키마 변경이 포함된 릴리즈에서는 롤백 전에 DB 백업 정책을 먼저 적용한다.

---

## 5) 장애 대응 최소 기준
- 증상/시간/영향 범위를 먼저 기록
- 로그 확인: `make logs ENV_FILE=.env`
- DB 연결/환경변수/포트 충돌 순으로 점검
- 임시 조치 후, 원인과 재발방지 항목을 `docs/`와 `README`에 반영

---

## 6) 운영 보안 체크
- `.env` 파일 권한 최소화 (`chmod 600 .env` 권장)
- 기본 비밀번호/placeholder 금지
- 서버 방화벽에서 필요한 포트만 오픈
- 정기적으로 비밀키 교체 (특히 AI API Key)
