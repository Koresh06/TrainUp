# Деплой TrainUp

Сервисы (`docker-compose.yml`): `db`, `redis`, `bot`, `worker`, `scheduler`,
`webhook` (FastAPI: webhook ЮKassa + страница возврата) и `caddy` (HTTPS-прокси
на webhook, сертификат Let's Encrypt выпускается и продлевается автоматически).

На сервере в одной папке лежат `docker-compose.yml`, `Caddyfile`, `Makefile` и `.env`.
Список команд управления: `make`.
Образ `ghcr.io/koresh06/trainup:latest` собирается GitHub Actions при push в `main`
(после зелёного CI).

## Первый запуск HTTPS для webhook

1. DNS: A-запись `bot` → IP сервера (домен задаётся `WEBHOOK_DOMAIN` в `.env`,
   по умолчанию `bot.24timekeep.ru`). Проверка: `dig +short bot.24timekeep.ru`
   совпадает с `curl -4 -s ifconfig.me`.
2. Порты 80 и 443 свободны (`ss -ltnp | grep -E ':(80|443)\s'` — пусто) и открыты
   в firewall (`ufw allow 80/tcp && ufw allow 443/tcp`) и в группе безопасности
   облачного провайдера.
3. В `.env`:
   ```env
   WEBHOOK_DOMAIN=bot.24timekeep.ru
   APP_CONFIG__PAYMENT__YOOKASSA__ENABLED=True
   APP_CONFIG__PAYMENT__YOOKASSA__RETURN_URL=https://bot.24timekeep.ru/payment/return
   ```
4. `docker compose up -d` → `docker compose logs caddy | grep -i certificate`
   («certificate obtained successfully»).
5. Проверка: `curl https://bot.24timekeep.ru/health` → `{"status":"ok"}`.
6. Кабинет ЮKassa → Интеграция → HTTP-уведомления:
   `https://bot.24timekeep.ru/webhook/yookassa`, события `payment.succeeded`
   и `payment.canceled`.

## Обновление

```bash
make update   # бэкап, образ, миграции, запуск
docker compose logs bot webhook | grep Payments   # какие способы оплаты подхватились
```

Миграции не запускаются сами: `make update` или `make migrate` при каждом обновлении, иначе
бот упадёт на новых таблицах и колонках. После миграции подтверждения тренеров
работающие тренеры остаются подтверждёнными, а новые ждут решения админа
(`APP_CONFIG__BUSINESS__TRAINER_APPROVAL_REQUIRED=False` выключает проверку).

Настройки читаются один раз при старте процесса — после правки `.env`
всегда `docker compose up -d`.

## Откат

```bash
docker compose stop bot worker scheduler webhook
# в docker-compose.yml: image: ghcr.io/koresh06/trainup:<sha прошлой версии>
docker compose run --rm bot alembic downgrade <ревизия прошлой версии>
docker compose up -d
```
Миграции с переносом данных схему откатывают, данные — нет; для полного отката
`make restore f=backups/<файл>.dump`.
