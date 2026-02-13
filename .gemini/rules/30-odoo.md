# 30 Odoo — owner_os_mgmt module + API routes

## Твоя зона ответственности
Реализовать кастомный Odoo модуль `owner_os_mgmt`:
- Модели: mgmt.transaction, mgmt.planned_payment, mgmt.expected_inflow (поля/статусы строго по ТЗ)
- Views: формы/списки/фильтры/экспорт CSV
- HTTP endpoints: /owner_os/api/v1/* (см. Odoo Integration Spec)
- Сервисный пользователь и права доступа для backend

## Что читать в архиве проекта
- 03-Data-Model.md
- 15-Odoo-Integration-Spec.md
- 13-Categories.md
- 14-Directions-Projects-Templates.md
- 12-Backlog.csv (EPIC-A)
- Официальная dev-документация Odoo (ORM, web-контроллеры, best practices): https://www.odoo.com/documentation/19.0/developer.html

## Технические требования
- Ошибки: единый формат error response.
- Idempotency: поле idempotency_key и/или предотвращение дублей.
- Обязательная связь Project → Direction (один direction на проект).
- Не полагаться на legacy RPC как на основной интеграционный путь.

## Ожидаемый результат
- Модуль + контроллеры API + базовые тесты
- Док установки/настройки service user
- Smoke checklist для ручной проверки
