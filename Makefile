COMPOSE_FILE=infra/docker-compose.yml
ENV_FILE=.env.example

.PHONY: up down logs ps migrate seed restart

up:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up -d

down:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down

restart:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) restart

logs:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) logs -f --tail=200

ps:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) ps

migrate:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) exec backend alembic upgrade head

seed:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) exec -T postgres \
		psql -U $${POSTGRES_USER:-aiops} -d $${POSTGRES_DB:-ai_ops_mvp_dev} \
		< backend/scripts/seed_safe_8k.sql
