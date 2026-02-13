# 70 Assistant NLU — intents, extraction, clarification

## Твоя зона ответственности
Сделать спецификацию понимания команд на русском:
- интенты (12)
- извлечение сущностей (amount/date/project/category/account/counterparty)
- confidence и правила уточнений
- формат confirm карточек + deep-link "Изменить" в Mini App
- набор тестовых фраз (>= 100) с ожидаемым нормализованным JSON payload

## Что читать в архиве проекта
- 09-Assistant-Intents.md
- 16-Assistant-UX.md
- 13-Categories.md (aliases)
- 14-Directions-Projects-Templates.md (aliases)
- 05-Security-RBAC.md

## Ожидаемый результат
- NLU Spec (heuristics + fallback)
- Test set (фраза → JSON)
- Рекомендации по обновлению aliases из UI
