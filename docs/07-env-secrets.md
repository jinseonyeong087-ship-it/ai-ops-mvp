# 07-env-secrets.md

운영/개발 환경에서 환경변수와 비밀값을 안전하게 다루기 위한 기준 문서입니다.

## 1) 원칙

- `.env`는 로컬/서버에서만 보관하고 Git에 커밋하지 않는다.
- 저장소에는 `.env.example`만 커밋한다.
- 운영 배포 전 `make validate-env-prod`로 placeholder/누락을 차단한다.
- 비밀값(특히 `POSTGRES_PASSWORD`, `AI_API_KEY`)은 강한 값으로 교체한다.

## 2) 파일 역할

- `.env.example` : 템플릿(민감정보 없음)
- `.env` : 실제 실행값(민감정보 포함 가능, 반드시 비공개)

## 3) 필수 키

- `APP_ENV`
- `API_PORT`
- `DATABASE_URL`
- `POSTGRES_PASSWORD`

운영(Production)에서는 아래 placeholder 금지:

- `POSTGRES_PASSWORD=__REPLACE_WITH_STRONG_PASSWORD__`
- `AI_API_KEY=__SET_LOCALLY__`

## 4) 검증 명령

```bash
# 개발 기준 검증
make validate-env

# 운영 기준 검증 (placeholder 차단)
make validate-env-prod ENV_FILE=.env.production
```

## 5) Docker Compose 정책

`infra/docker-compose.yml`에서 아래 항목은 필수값으로 강제한다.

- `POSTGRES_PASSWORD`
- `DATABASE_URL`

누락 시 compose 단계에서 실패하도록 구성해 잘못된 배포를 빠르게 차단한다.
