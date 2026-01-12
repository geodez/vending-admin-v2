-- Создание первого пользователя (Owner)
-- Telegram User ID: 602720033

INSERT INTO users (telegram_user_id, username, first_name, role, is_active)
VALUES (602720033, 'owner', 'Owner', 'owner', true)
ON CONFLICT (telegram_user_id) DO UPDATE
SET 
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Проверка созданного пользователя
SELECT id, telegram_user_id, username, first_name, role, is_active, created_at
FROM users
WHERE telegram_user_id = 602720033;
