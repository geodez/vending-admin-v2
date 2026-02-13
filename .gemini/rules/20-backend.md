# 20 Backend — FastAPI (BFF + ассистент + RBAC)

## Твоя зона ответственности
Реализовать backend на Python 3.12 + FastAPI:
- Auth: Telegram initData validation → JWT
- RBAC: users, project ACL, entity permissions
- Audit log
- Draft/Confirm flow (Inbox)
- Telegram webhook: text/voice/photo → intent → draft_action
- Odoo connector: вызовы Odoo endpoints, ретраи, идемпотентность
- Dashboards aggregation endpoints

## Что читать в архиве проекта
- 10-OpenAPI.yaml
- 04-APIs.md
- 11-AppDB-DDL.sql
- 05-Security-RBAC.md
- 09-Assistant-Intents.md
- 16-Assistant-UX.md
- 17-Media-Pipeline.md
- 15-Odoo-Integration-Spec.md
- 18-DoD-Repo-Env.md
- 12-Backlog.csv (EPIC-B, EPIC-C)
- Для интеграции с Odoo и спорных поведенческих вопросов использовать как источник истины: https://www.odoo.com/documentation/19.0/developer.html

## Технические требования
- Alembic миграции для app DB (или аккуратный импорт DDL → ORM).
- Строгая серверная валидация initData.
- Финансы по умолчанию: draft_only. Любое confirm → audit_event.
- Idempotency-Key на критичные create/confirm.
- Структурированное логирование (request_id, user_id, draft_id).

## Ожидаемый результат
- Рабочий backend, соответствующий OpenAPI (или обновлённый OpenAPI + changelog)
- Миграции + сиды (assistant_permissions дефолты)
- Unit tests: auth, rbac, drafts, odoo connector
- Инструкции запуска (local + env)
