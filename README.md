# Copyright 2024 Egor Filimonov, filimoneg@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://apache.org
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# NSA
[![CI Integration](https://github.com/NSA-Filimonov/NSA/actions/workflows/ci-integration.yml/badge.svg?branch=main)](https://github.com/NSA-Filimonov/NSA/actions/workflows/ci-integration.yml)
#New System Autentification. Software for replacing passwords, PINs, and patterns.
#
#
# NSA Backend v1.2 (Smoke Passed) / NSA Backend v1.2 (Smoke пройден)
> Status / Статус: **v1.2 demo-ready (pre-hardening)**
---
## EN
### Overview
## CI/CD
markdown## CI/CD
The project uses the GitHub Actions workflow `ci-integration.yml`.

### What the pipeline does
- Builds the Docker environment (`docker-compose.prod.yml`)
- Spins up services (`redis`, `api`, `nginx`)
- Runs integration tests (`pytest -m integration`)
- Saves the JUnit report (`test-results/junit.xml`) as an artifact
- Dumps container logs on failure
- Performs a teardown (`docker compose down -v --remove-orphans`)

### Triggers
- `push` to `main`
- `pull_request` to `main`
- Manual trigger (`workflow_dispatch`)
Проект использует GitHub Actions workflow: `.github/workflows/ci-integration.yml`.
### Что делает pipeline
- Собирает Docker-окружение на базе `docker-compose.prod.yml`
- Поднимает сервисы (`redis`, `api`, `nginx`)
- Запускает интеграционные тесты (`pytest -m integration`)
- Формирует JUnit-отчёт (`test-results/junit.xml`) и публикует его как artifact
- При падении тестов сохраняет логи контейнеров
- Выполняет очистку окружения (`docker compose down -v --remove-orphans`)
### Когда запускается
- При `push` в ветку `main`
- При `pull_request` в ветку `main`
- Вручную через `workflow_dispatch`
### Артефакты
- `junit-integration-report` — XML-отчёт тестов в формате JUnit
### Покрытие тестов
Для бейджа покрытия используется Codecov.
Pipeline генерирует `coverage.xml` и отправляет его в Codecov, после чего бейдж обновляется автоматически.
## #
NSA Backend is a FastAPI + Redis service that implements a challenge/verify flow with temporary lockout policy and smoke-tested production compose setup.
Current release status:
- ✅ Redis-backed state
- ✅ Centralized input validation
- ✅ Docker Compose production flow
- ✅ Smoke checks passed
- ⏳ Hardening & Ops (TLS, rate-limit, fail2ban, metrics, CI/CD) planned next
### Key Features
- `POST /setup/start` — starts setup session
- `POST /setup/secret` — stores user secret profile
- `POST /challenge/create` — creates one-time challenge
- `POST /challenge/verify` — verifies answer and applies lockout policy
- `GET /health` — health endpoint
### Security Logic (current)
- One-time challenge usage (`GETDEL` in Redis)
- TTL-based lifecycle for setup/challenge/lock/fail counters
- Temporary lock after too many failed attempts
- Validation for `user_id`, `grid_size`, `steps`, `response`
### Tech Stack
- Python 3.11+
- FastAPI
- Redis (async `redis-py` 5.x)
- Nginx (reverse proxy)
- Docker Compose
### Project Structure
- `app/main.py` — app entrypoint
- `app/routers/setup.py` — setup routes
- `app/routers/auth.py` — challenge/auth routes
- `app/core/validation.py` — centralized validation module
- `docker-compose.prod.yml` — production compose file
- `scripts/smoke_prod.sh` — smoke test script
- `Makefile` — operational commands
### Quick Start
```bash
make prod-up
make prod-ps
make prod-check

Logs:

make prod-logs

Stop:

make prod-down

Smoke Test

make prod-smoke

Expected result:

🎉 Smoke checks passed

Make Targets

    make prod-up — build + run prod stack
    make prod-down — stop stack
    make prod-logs — follow logs
    make prod-ps — container status
    make prod-restart — full restart with rebuild
    make prod-smoke — smoke tests
    make prod-check — quick health check

Current Limitations

This commit intentionally does not include full hardening yet:
- no TLS/Let’s Encrypt
- no Nginx rate limiting rules in production
- no fail2ban
- no Prometheus/Grafana stack
- no GitHub Actions deployment pipeline

These items are planned for v1.2 hardening + ops.
Acceptance Criteria (for this milestone)

Milestone is considered complete if:
1. make prod-up starts services successfully
2. make prod-check returns healthy status
3. make prod-smoke ends with 🎉 Smoke checks passed


RU
Обзор

NSA Backend — это сервис на FastAPI + Redis, реализующий сценарий challenge/verify с политикой временной блокировки и проверенным prod-контуром через Docker Compose.

Текущий статус релиза:
- ✅ Состояние хранится в Redis
- ✅ Централизованная валидация входных данных
- ✅ Прод-контур на Docker Compose
- ✅ Smoke-проверки пройдены
- ⏳ Hardening & Ops (TLS, rate-limit, fail2ban, метрики, CI/CD) — следующий этап
Основные возможности

    POST /setup/start — запуск setup-сессии
    POST /setup/secret — сохранение секретного профиля пользователя
    POST /challenge/create — создание одноразового challenge
    POST /challenge/verify — проверка ответа и применение lockout-политики
    GET /health — endpoint проверки здоровья сервиса

Текущая логика безопасности

    Одноразовый challenge (GETDEL в Redis)
    TTL-жизненный цикл setup/challenge/lock/fail счётчиков
    Временная блокировка после серии неудачных попыток
    Валидация user_id, grid_size, steps, response

Технологии

    Python 3.11+
    FastAPI
    Redis (async redis-py 5.x)
    Nginx (reverse proxy)
    Docker Compose

Структура проекта

    app/main.py — точка входа приложения
    app/routers/setup.py — setup-роуты
    app/routers/auth.py — challenge/auth-роуты
    app/core/validation.py — централизованный модуль валидации
    docker-compose.prod.yml — продовый compose-файл
    scripts/smoke_prod.sh — smoke-скрипт
    Makefile — операционные команды

Быстрый запуск

make prod-up
make prod-ps
make prod-check

Логи:

make prod-logs

Остановка:

make prod-down

Smoke-проверка

make prod-smoke

Ожидаемый результат:

🎉 Smoke checks passed

Команды Makefile

    make prod-up — собрать и поднять прод-контур
    make prod-down — остановить контур
    make prod-logs — смотреть логи
    make prod-ps — статус контейнеров
    make prod-restart — полный рестарт с пересборкой
    make prod-smoke — smoke-тесты
    make prod-check — быстрая проверка health

Ограничения текущего релиза

Этот коммит намеренно не включает полный hardening:
- нет TLS/Let’s Encrypt
- нет production rate-limit правил Nginx
- нет fail2ban
- нет Prometheus/Grafana
- нет GitHub Actions pipeline для деплоя

Эти задачи запланированы на этап v1.2 hardening + ops.
Критерии готовности (для этого этапа)

Этап считается завершённым, если:
1. make prod-up успешно поднимает сервисы
2. make prod-check возвращает healthy
3. make prod-smoke завершается с 🎉 Smoke checks passed