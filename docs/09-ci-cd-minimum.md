# 09-ci-cd-minimum.md

## 목적
MVP 단계에서 배포 전 최소 품질을 보장하기 위한 CI 기준을 정의한다.

## 파이프라인 파일
- `.github/workflows/ci.yml`

## 트리거
- `push` to `main`
- `pull_request`

## 잡 구성
1. `backend-smoke`
   - Python 3.12
   - `pip install -r backend/requirements.txt`
   - `backend/scripts/smoke_test.sh` 실행
2. `frontend-build`
   - Node 20
   - `npm ci`
   - `npm run lint`
   - `npm run build`

## 품질 게이트
- 두 잡 모두 성공해야 머지/배포 후보로 인정
- 실패 시 원인 수정 후 재실행

## 추후 확장
- DB 포함 통합 테스트
- 보안 스캔(SAST/dependency audit)
- staging 자동 배포 및 승인 기반 prod 배포
