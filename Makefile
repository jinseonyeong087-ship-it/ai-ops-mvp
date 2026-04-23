# AI Ops MVP 로컬 운영 명령 모음
# - 동일 명령을 팀원 모두 같은 방식으로 실행하도록 표준화

COMPOSE_FILE=infra/docker-compose.yml
ENV_FILE?=.env

.PHONY: init-env check-env up down logs ps migrate seed restart smoke

# .env 초기 생성 (.env.example 기반)
init-env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "[ok] .env created from .env.example"; else echo "[skip] .env already exists"; fi

# 실행 전 필수 파일(.env) 존재 확인
check-env:
	@if [ ! -f $(ENV_FILE) ]; then echo "[error] $(ENV_FILE) not found. run: make init-env"; exit 1; fi

# postgres + backend 컨테이너 기동
up: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up -d

# 컨테이너 종료
down: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down

# 컨테이너 재시작
restart: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) restart

# 실시간 로그 확인
logs: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) logs -f --tail=200

# 컨테이너 상태 확인
ps: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) ps

# DB 마이그레이션 적용
migrate: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) exec backend alembic upgrade head

# 시드 데이터 입력
seed: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) exec -T postgres \
		psql -U $${POSTGRES_USER:-aiops} -d $${POSTGRES_DB:-ai_ops_mvp_dev} \
		< backend/scripts/seed_safe_8k.sql

# 핵심 API 스모크 테스트
smoke:
	./backend/scripts/smoke_test.sh
