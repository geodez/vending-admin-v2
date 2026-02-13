# Быстрая инструкция: Настройка Telegram бота

## Проблема
При входе через Telegram появляется ошибка **"Bot domain invalid"**

## Решение (5 минут)

### Шаг 1: Откройте BotFather
1. Откройте Telegram
2. Найдите [@BotFather](https://t.me/BotFather)
3. Нажмите "Start" или отправьте `/start`

### Шаг 2: Настройте домен
1. Отправьте команду: `/setdomain`
2. Выберите вашего бота: `@coffeekznebot`
3. Введите домен (БЕЗ https://):
   ```
   romanrazdobreev.store
   ```

### Шаг 3: Проверьте
1. Откройте https://romanrazdobreev.store
2. Нажмите на кнопку входа через Telegram
3. Ошибка "Bot domain invalid" должна исчезнуть

## Важно!
- ❌ НЕ указывайте `https://romanrazdobreev.store`
- ✅ Указывайте только `romanrazdobreev.store`
- ⚠️ Telegram разрешает только ОДИН домен для бота

## Что дальше?
После настройки домена вы сможете:
- ✅ Входить через Telegram Login Widget (в браузере)
- ✅ Входить через Telegram Mini App
- ✅ Входить через Email/Пароль (новая функция)

---

**Полная документация:** См. `docs/AUTHENTICATION.md`
