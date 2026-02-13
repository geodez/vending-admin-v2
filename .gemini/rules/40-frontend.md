# 40 Frontend — Telegram Mini App (React)

## Твоя зона ответственности
Реализовать Mini App на React 18 + TS + Vite + Zustand + Ant Design (минималистично):
Экраны MVP:
- Owner Dashboard
- Project Health
- Forecast
- Inbox (draft confirm/edit/reject)
- Settings (assistant permissions matrix, aliases, RBAC users)

## Что читать в архиве проекта
- 01-PRD.md
- 10-OpenAPI.yaml
- 04-APIs.md
- 05-Security-RBAC.md
- 16-Assistant-UX.md
- 18-DoD-Repo-Env.md
- 12-Backlog.csv (EPIC-D)

## Технические требования
- Auth: Telegram initData → backend /auth/telegram → JWT
- Все финансовые действия только через Inbox (confirm/edit/reject)
- Минимум визуального шума: использовать ограниченный набор компонентов AntD
- Deep-link из Telegram карточки "Изменить" ведёт в Mini App на draft edit

## Ожидаемый результат
- Рабочее приложение + API client + state management
- Компоненты KPI и таблиц
- Инструкции сборки и env
