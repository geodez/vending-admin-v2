#!/usr/bin/env python3
"""
Скрипт для добавления стаканов и крышек во все рецепты.
На один напиток: 1 стакан и 1 крышка.
"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def find_ingredient_by_name(db_session, search_terms: list) -> str:
    """
    Находит ингредиент по ключевым словам в названии.
    Возвращает ingredient_code или None.
    """
    # Ищем по display_name_ru и ingredient_code
    for term in search_terms:
        result = db_session.execute(
            text("""
                SELECT ingredient_code, display_name_ru 
                FROM ingredients 
                WHERE LOWER(display_name_ru) LIKE LOWER(:term)
                   OR LOWER(ingredient_code) LIKE LOWER(:term)
                LIMIT 1
            """),
            {"term": f"%{term}%"}
        )
        row = result.fetchone()
        if row:
            return row[0]
    return None

def add_cups_and_lids_to_all_recipes():
    """Добавляет стаканы и крышки во все активные рецепты."""
    
    # Подключение к БД
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    try:
        # Ищем ингредиенты "стакан" и "крышка"
        cup_codes = ["стакан", "cup", "стаканчик"]
        lid_codes = ["крышка", "lid", "крышечка"]
        
        cup_ingredient_code = find_ingredient_by_name(db_session, cup_codes)
        lid_ingredient_code = find_ingredient_by_name(db_session, lid_codes)
        
        if not cup_ingredient_code:
            print("❌ Ошибка: не найден ингредиент 'стакан'")
            print("   Попробуйте найти его вручную и укажите ingredient_code")
            return
        
        if not lid_ingredient_code:
            print("❌ Ошибка: не найден ингредиент 'крышка'")
            print("   Попробуйте найти его вручную и укажите ingredient_code")
            return
        
        print(f"✓ Найден стакан: {cup_ingredient_code}")
        print(f"✓ Найдена крышка: {lid_ingredient_code}")
        
        # Получаем все активные рецепты
        result = db_session.execute(
            text("SELECT id, name FROM drinks WHERE is_active = true ORDER BY id")
        )
        drinks = result.fetchall()
        
        if not drinks:
            print("⚠ Нет активных рецептов")
            return
        
        print(f"\n📋 Найдено активных рецептов: {len(drinks)}")
        
        # Добавляем стаканы и крышки в каждый рецепт
        added_cups = 0
        added_lids = 0
        skipped_cups = 0
        skipped_lids = 0
        
        for drink_id, drink_name in drinks:
            # Проверяем, есть ли уже стакан в рецепте
            cup_check = db_session.execute(
                text("""
                    SELECT 1 FROM drink_items 
                    WHERE drink_id = :drink_id AND ingredient_code = :ingredient_code
                """),
                {"drink_id": drink_id, "ingredient_code": cup_ingredient_code}
            )
            
            if not cup_check.fetchone():
                # Добавляем стакан
                db_session.execute(
                    text("""
                        INSERT INTO drink_items (drink_id, ingredient_code, qty_per_unit, unit)
                        VALUES (:drink_id, :ingredient_code, 1, 'pcs')
                    """),
                    {
                        "drink_id": drink_id,
                        "ingredient_code": cup_ingredient_code
                    }
                )
                added_cups += 1
            else:
                skipped_cups += 1
            
            # Проверяем, есть ли уже крышка в рецепте
            lid_check = db_session.execute(
                text("""
                    SELECT 1 FROM drink_items 
                    WHERE drink_id = :drink_id AND ingredient_code = :ingredient_code
                """),
                {"drink_id": drink_id, "ingredient_code": lid_ingredient_code}
            )
            
            if not lid_check.fetchone():
                # Добавляем крышку
                db_session.execute(
                    text("""
                        INSERT INTO drink_items (drink_id, ingredient_code, qty_per_unit, unit)
                        VALUES (:drink_id, :ingredient_code, 1, 'pcs')
                    """),
                    {
                        "drink_id": drink_id,
                        "ingredient_code": lid_ingredient_code
                    }
                )
                added_lids += 1
            else:
                skipped_lids += 1
        
        # Сохраняем изменения
        db_session.commit()
        
        print(f"\n✅ Результаты:")
        print(f"   Стаканы: добавлено {added_cups}, пропущено {skipped_cups} (уже были)")
        print(f"   Крышки: добавлено {added_lids}, пропущено {skipped_lids} (уже были)")
        print(f"\n✓ Готово! Всего обработано рецептов: {len(drinks)}")
        
    except Exception as e:
        db_session.rollback()
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db_session.close()

if __name__ == "__main__":
    add_cups_and_lids_to_all_recipes()
