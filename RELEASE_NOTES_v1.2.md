---
### `RELEASE_NOTES_v1.2.md`
```md
# Release Notes — v1.2 / Примечания к релизу — v1.2
Release type / Тип релиза: **Demo-ready milestone (pre-hardening)**
Date / Дата: **2026-XX-XX**
---
## EN
### Summary
Version `v1.2` stabilizes core backend behavior and confirms production-flow operability by passing the full smoke test scenario.
### What’s Included
- Redis-based state management for setup/challenge/verification flow
- Centralized validation module (`app/core/validation.py`)
- Updated routers integrated with centralized validation:
  - `app/routers/setup.py`
  - `app/routers/auth.py`
- Operational Makefile targets for production workflow:
  - `prod-up`, `prod-down`, `prod-logs`, `prod-ps`, `prod-restart`, `prod-smoke`, `prod-check`
### Verification
Smoke test result:
- ✅ `health 200`
- ✅ setup flow (`/setup/start`, `/setup/secret`)
- ✅ challenge flow (`/challenge/create`, `/challenge/verify`)
- ✅ negative checks (non-digit, no-secret, challenge reuse)
- ✅ lockout policy behavior
- ✅ final status: `🎉 Smoke checks passed`
### Known Gaps (Intentionally Deferred)
- TLS/Let’s Encrypt
- Nginx rate-limiting policies (production hardened)
- fail2ban integration
- Prometheus/Grafana observability stack
- GitHub Actions deployment pipeline
These are scheduled for `v1.2 hardening + ops`.
### Risk Note
Current release is suitable for demo and controlled deployment environments. Full internet-facing production hardening is pending.
### Next Milestone
`v1.2 hardening + ops`:
1. TLS + auto-renew certs
2. Nginx rate-limit + brute-force mitigation
3. Structured JSON logs
4. Metrics + alerts
5. CI/CD deploy with post-deploy smoke + rollback
---
## RU
### Кратко
Версия `v1.2` стабилизирует ключевую логику бэкенда и подтверждает работоспособность прод-контура через успешное прохождение полного smoke-сценария.
### Что вошло в релиз
- Хранение состояния в Redis для setup/challenge/verify
- Централизованный модуль валидации (`app/core/validation.py`)
- Обновлённые роутеры с интеграцией новой валидации:
  - `app/routers/setup.py`
  - `app/routers/auth.py`
- Операционные цели в Makefile для prod-сценариев:
  - `prod-up`, `prod-down`, `prod-logs`, `prod-ps`, `prod-restart`, `prod-smoke`, `prod-check`
### Проверка качества
Результат smoke-тестов:
- ✅ `health 200`
- ✅ setup-сценарий (`/setup/start`, `/setup/secret`)
- ✅ challenge-сценарий (`/challenge/create`, `/challenge/verify`)
- ✅ негативные проверки (нецифровой ответ, отсутствие секрета, повтор challenge)
- ✅ корректная lockout-политика
- ✅ финальный статус: `🎉 Smoke checks passed`
### Известные ограничения (осознанно отложены)
- TLS/Let’