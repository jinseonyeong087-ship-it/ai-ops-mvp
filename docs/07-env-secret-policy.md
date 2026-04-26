# 07-env-secret-policy.md

## 목적
운영/개발 환경에서 환경변수와 비밀값(Secret)을 안전하게 관리하기 위한 최소 기준을 정의한다.

## 원칙
1. 비밀값은 Git에 커밋하지 않는다.
2. `.env.example`에는 placeholder만 둔다.
3. 실제 `.env`는 로컬/서버에만 존재한다.
4. 실행 전 `scripts/validate_env.sh`로 필수값과 placeholder를 검증한다.

## 파일 규칙
- 추적 대상: `.env.example`
- 비추적 대상: `.env`, `.env.*` (`.gitignore` 적용)

## 필수 키
- `APP_ENV`
- `API_PORT`
- `DATABASE_URL`
- `POSTGRES_PASSWORD`

## 운영 배포 전 검증
```bash
make validate-env-prod
```
- placeholder(`__REPLACE_WITH_STRONG_PASSWORD__`, `__SET_LOCALLY__`)가 남아 있으면 실패해야 한다.

## Docker Compose 가드
`infra/docker-compose.yml`에서 다음 값은 필수로 강제한다.
- `POSTGRES_PASSWORD`
- `DATABASE_URL`

누락 시 compose 실행이 실패해야 하며, 이를 통해 잘못된 기본값으로 운영되는 사고를 방지한다.
