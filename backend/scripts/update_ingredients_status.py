#!/usr/bin/env python3
"""
Скрипт для обновления статусов ингредиентов:
- Ингредиенты, используемые в рецептах: is_active = true, expense_kind = 'stock_tracked'
- Остальные ингредиенты: is_active = false, expense_kind = 'not_tracked'
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def update_ingredients_status():
    """Обновляет статусы ингредиентов на основе их использования в рецептах."""
    
    # Создаем подключение к БД
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    try:
        print("=" * 80)
        print("ОБНОВЛЕНИЕ СТАТУСОВ ИНГРЕДИЕНТОВ")
        print("=" * 80)
        
        # Получаем список ингредиентов, используемых в рецептах
        result = db_session.execute(text("""
            SELECT DISTINCT ingredient_code 
            FROM drink_items
        """))
        used_ingredients = {row[0] for row in result}
        
        print(f"\n📋 Найдено ингредиентов, используемых в рецептах: {len(used_ingredients)}")
        if used_ingredients:
            print("   Используемые ингредиенты:")
            for code in sorted(used_ingredients):
                print(f"     - {code}")
        
        # Получаем общее количество ингредиентов
        total_result = db_session.execute(text("SELECT COUNT(*) FROM ingredients"))
        total_count = total_result.scalar()
        print(f"\n📊 Всего ингредиентов в базе: {total_count}")
        
        # Обновляем ингредиенты, используемые в рецептах
        if used_ingredients:
            placeholders = ','.join([f"'{code}'" for code in used_ingredients])
            update_used = db_session.execute(text(f"""
                UPDATE ingredients
                SET is_active = true,
                    expense_kind = 'stock_tracked'
                WHERE ingredient_code IN ({placeholders})
            """))
            print(f"\n✅ Обновлено используемых ингредиентов: {update_used.rowcount}")
            print("   Установлено: is_active = true, expense_kind = 'stock_tracked'")
        
        # Обновляем остальные ингредиенты
        if used_ingredients:
            placeholders = ','.join([f"'{code}'" for code in used_ingredients])
            update_unused = db_session.execute(text(f"""
                UPDATE ingredients
                SET is_active = false,
                    expense_kind = 'not_tracked'
                WHERE ingredient_code NOT IN ({placeholders})
            """))
        else:
            # Если нет используемых ингредиентов, обновляем все
            update_unused = db_session.execute(text("""
                UPDATE ingredients
                SET is_active = false,
                    expense_kind = 'not_tracked'
            """))
        
        print(f"✅ Обновлено неиспользуемых ингредиентов: {update_unused.rowcount}")
        print("   Установлено: is_active = false, expense_kind = 'not_tracked'")
        
        # Коммитим изменения
        db_session.commit()
        
        # Проверяем результаты
        print("\n" + "=" * 80)
        print("ПРОВЕРКА РЕЗУЛЬТАТОВ")
        print("=" * 80)
        
        check_result = db_session.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE is_active = true AND expense_kind = 'stock_tracked') as active_tracked,
                COUNT(*) FILTER (WHERE is_active = false AND expense_kind = 'not_tracked') as inactive_not_tracked,
                COUNT(*) as total
            FROM ingredients
        """))
        row = check_result.fetchone()
        active_tracked, inactive_not_tracked, total = row
        
        print(f"\n📊 Итоговая статистика:")
        print(f"   Активных и учитываемых: {active_tracked}")
        print(f"   Неактивных и не учитываемых: {inactive_not_tracked}")
        print(f"   Всего: {total}")
        
        # Показываем список активных ингредиентов
        active_result = db_session.execute(text("""
            SELECT ingredient_code, display_name_ru
            FROM ingredients
            WHERE is_active = true AND expense_kind = 'stock_tracked'
            ORDER BY ingredient_code
        """))
        print(f"\n✅ Активные и учитываемые ингредиенты ({active_tracked}):")
        for row in active_result:
            print(f"     - {row[0]}: {row[1] or 'N/A'}")
        
        print("\n" + "=" * 80)
        print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("=" * 80)
        
    except Exception as e:
        db_session.rollback()
        print(f"\n❌ Ошибка: {e}")
        raise
    finally:
        db_session.close()

if __name__ == "__main__":
    update_ingredients_status()
