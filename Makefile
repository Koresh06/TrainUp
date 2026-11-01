# Управление TrainUp. Список команд: make
# Сервер: Makefile лежит рядом с docker-compose.yml и .env.
# Параметры: s=сервис, n=строк, q=текст, f=файл, например make logs s=bot n=500

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE := docker compose
# приложение без db/redis/caddy: их останавливать при обновлении не нужно
APP_SERVICES := bot worker scheduler webhook
BACKUP_DIR := backups

s ?=
n ?= 200
q ?=
f ?=

# данные берём из окружения контейнера db, на хосте их может не быть
define db_sql
$(COMPOSE) exec -T db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" $(1)'
endef

define STATS_SQL
SELECT 'Тренеры: подтверждены' AS "Показатель", count(*) FROM trainers WHERE approval_status = 'APPROVED'
UNION ALL SELECT 'Тренеры: ждут решения', count(*) FROM trainers WHERE approval_status = 'PENDING'
UNION ALL SELECT 'Тренеры: отклонены', count(*) FROM trainers WHERE approval_status = 'REJECTED'
UNION ALL SELECT 'Активные подписки', count(DISTINCT trainer_id) FROM trainer_subscriptions WHERE status = 'ACTIVE' AND expired_at > now()
UNION ALL SELECT 'Клиенты', count(*) FROM clients
UNION ALL SELECT 'Записи на тренировки', count(*) FROM bookings
UNION ALL SELECT 'Оплаты: прошли', count(*) FROM payments WHERE status = 'PAID'
UNION ALL SELECT 'Оплаты: ждут', count(*) FROM payments WHERE status = 'PENDING'
UNION ALL SELECT 'Админы в базе', count(*) FROM bot_admins
UNION ALL SELECT 'Пользователи бота', count(*) FROM bot_users
UNION ALL SELECT 'Активны за сутки', count(*) FROM bot_users WHERE last_activity_at > now() - interval '1 day'
UNION ALL SELECT 'Заблокировали бота', count(*) FROM bot_users WHERE blocked_at IS NOT NULL;
endef
export STATS_SQL

.PHONY: help
help: ## Показать эту справку
	@awk 'BEGIN {FS = ":.*## "} \
		/^##@/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 5)} \
		/^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf '\nПримеры: make logs s=bot n=500, make grep q=ReviewTrainer, make restore f=backups/x.dump\n'

##@ Разработка (локально, через uv)

.PHONY: install dev-bot dev-worker dev-scheduler dev-webhook test test-fast lint fix check revision
install: ## Поставить зависимости и pre-commit
	uv sync
	uv run pre-commit install

dev-bot: ## Запустить бота
	uv run python -m src.presentation.telegram.app

dev-worker: ## Запустить воркер фоновых задач
	uv run taskiq worker src.worker:broker

dev-scheduler: ## Запустить планировщик
	uv run taskiq scheduler src.scheduler:scheduler

dev-webhook: ## Запустить webhook ЮKassa на порту 8080
	uv run uvicorn src.presentation.web.app:create_app --port 8080 --factory

test: ## Все тесты
	uv run pytest -q

test-fast: ## Тесты до первого падения, q=фильтр по имени
	uv run pytest -q -x $(if $(q),-k "$(q)")

lint: ## Проверить код ruff
	uv run ruff check src tests

fix: ## Исправить что можно автоматически
	uv run ruff check src tests --fix

check: lint test ## ruff и тесты

revision: ## Новая миграция, q="описание"
	@test -n "$(q)" || { echo 'Укажите описание: make revision q="add something"'; exit 1; }
	uv run alembic revision --autogenerate -m "$(q)"

##@ Состояние (сервер)

.PHONY: ps health stats top disk version
ps: ## Статус контейнеров
	$(COMPOSE) ps

health: ## Здоровье БД, Redis и webhook
	@$(COMPOSE) exec -T db sh -c 'pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' || true
	@printf 'Redis: '; $(COMPOSE) exec -T redis redis-cli ping || true
	@printf 'Webhook: '; curl -fsS -m 5 http://127.0.0.1:8080/health || echo 'не отвечает'
	@echo

stats: ## Сводка: тренеры, подписки, клиенты, оплаты
	@echo "$$STATS_SQL" | $(call db_sql,)

top: ## Потребление CPU и памяти
	docker stats --no-stream

disk: ## Место: диск, логи, бэкапы, образы
	@df -h .
	@du -sh logs $(BACKUP_DIR) 2>/dev/null || true
	@docker system df

version: ## Какой образ запущен и текущая миграция
	@$(COMPOSE) images
	@$(COMPOSE) exec -T bot alembic current

##@ Логи (сервер)

.PHONY: logs tail errors grep
logs: ## Логи и слежение, s=сервис n=строк
	$(COMPOSE) logs -f --tail=$(n) $(s)

tail: ## Логи без слежения, s=сервис n=строк
	$(COMPOSE) logs --tail=$(n) $(s)

errors: ## Следить за WARNING и ошибками всех сервисов
	tail -n $(n) -F logs/errors.log

grep: ## Поиск по файлам логов, q=текст
	@test -n "$(q)" || { echo 'Укажите текст: make grep q=ReviewTrainer'; exit 1; }
	@grep -rhF -- '$(q)' logs | sort | tail -n $(n)

##@ Управление (сервер)

.PHONY: up stop restart pull update
up: ## Запустить всё и перечитать .env
	$(COMPOSE) up -d

stop: ## Остановить приложение, БД и Redis продолжат работать
	$(COMPOSE) stop $(APP_SERVICES)

restart: ## Пересоздать сервисы и перечитать .env, s=сервис
	$(COMPOSE) up -d --force-recreate $(if $(s),$(s),$(APP_SERVICES))

pull: ## Скачать свежий образ
	$(COMPOSE) pull

update: backup ## Обновить: бэкап, образ, миграции, запуск
	$(COMPOSE) pull
	$(COMPOSE) stop $(APP_SERVICES)
	$(COMPOSE) run --rm bot alembic upgrade head
	$(COMPOSE) up -d
	$(COMPOSE) ps

##@ База и данные (сервер)

.PHONY: migrate migrations psql redis shell backup backups restore
migrate: ## Применить миграции
	$(COMPOSE) run --rm bot alembic upgrade head

migrations: ## Текущая миграция и история
	$(COMPOSE) run --rm bot sh -c 'alembic current && alembic history | head -n 10'

psql: ## Консоль PostgreSQL
	$(COMPOSE) exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

redis: ## Консоль Redis
	$(COMPOSE) exec redis redis-cli

shell: ## Shell в контейнере, s=сервис (по умолчанию bot)
	$(COMPOSE) exec $(if $(s),$(s),bot) sh

backup: ## Бэкап БД в backups/
	@mkdir -p $(BACKUP_DIR)
	@file=$(BACKUP_DIR)/trainup_$$(date +%F_%H%M%S).dump; \
	$(COMPOSE) exec -T db sh -c 'pg_dump -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -Fc' > "$$file.tmp" \
		|| { rm -f "$$file.tmp"; echo 'Бэкап не создан'; exit 1; }; \
	mv "$$file.tmp" "$$file"; \
	echo "Бэкап: $$file ($$(du -h "$$file" | cut -f1))"

backups: ## Список бэкапов
	@ls -lh $(BACKUP_DIR) 2>/dev/null || echo 'Бэкапов нет'

restore: ## Восстановить БД, f=файл (заменит текущие данные)
	@test -f "$(f)" || { echo 'Укажите файл: make restore f=backups/x.dump'; exit 1; }
	@read -r -p "Заменить текущую базу данными из $(f)? Введите restore: " answer; \
		test "$$answer" = restore || { echo 'Отменено'; exit 1; }
	$(COMPOSE) stop $(APP_SERVICES)
	$(COMPOSE) exec -T db sh -c 'pg_restore -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" --clean --if-exists --no-owner' < "$(f)"
	$(COMPOSE) up -d
