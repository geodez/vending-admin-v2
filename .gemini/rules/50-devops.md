# 50 DevOps — VPS, Docker Compose, TLS, encrypted backups, monitoring

## Твоя зона ответственности
Поднять прод-контур на VPS firstvds.ru:
- Odoo + postgres_odoo
- FastAPI + postgres_app
- Nginx reverse proxy + TLS (Let's Encrypt)
- Encrypted backups (age/gpg) + offsite + retention
- Monitoring/alerts + runbook restore

## Что читать в архиве проекта
- 08-DevOps-Runbook.md
- 18-DoD-Repo-Env.md
- 05-Security-RBAC.md
- 12-Backlog.csv (EPIC-E)

## Технические требования
- Секреты не коммитить.
- Backup scripts должны быть идемпотентными, логировать результат и код возврата.
- Restore test monthly: инструкции + командный файл.

## Ожидаемый результат
- docker-compose.yml (prod) + override (dev/staging)
- nginx configs + TLS automation
- scripts: backup, restore
- monitoring config + runbook
