# Настройка Telegram Bot для Login Widget

## Проблема: "Bot domain invalid"

Эта ошибка возникает, когда домен вашего приложения не добавлен в настройки Telegram бота.

## Решение

### 1. Откройте BotFather в Telegram

Найдите [@BotFather](https://t.me/BotFather) в Telegram

### 2. Настройте домен для Login Widget

```
/setdomain
```

Выберите вашего бота (например, `@coffeekznebot`)

### 3. Укажите домен

Введите домен БЕЗ протокола (http/https):

**Для production:**
```
romanrazdobreev.store
```

**Для локальной разработки (если нужно):**
```
localhost
```

⚠️ **Важно:** 
- Домен должен быть БЕЗ `https://` или `http://`
- Для локальной разработки Telegram может не разрешить `localhost` - используйте ngrok или другой туннель
- Можно указать только ОДИН домен за раз

### 4. Проверьте настройки

После настройки домена, Telegram Login Widget должен работать на указанном домене.

## Альтернативное решение: Авторизация по логину/паролю

Если вы не хотите использовать Telegram Login Widget, можно использовать авторизацию по логину и паролю (см. документацию по авторизации).

## Текущая конфигурация

- **Bot Username:** `coffeekznebot` (из `.env.example`)
- **Требуемый домен:** `romanrazdobreev.store`

## Дополнительные ресурсы

- [Telegram Login Widget Documentation](https://core.telegram.org/widgets/login)
- [Telegram Bot API](https://core.telegram.org/bots/api)
