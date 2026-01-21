#!/usr/bin/env python3
"""
Скрипт импорта рецептов из JSON файлов.

Этап 1: Создание рецептов напитков и их состава (без привязки к терминалам).

Использование:
    python import_recipes_from_json.py --product-file 2025_12_29_19_14_product.json --recipe-file 2025_12_29_19_14_recipe.json
"""

import json
import sys
import os
import argparse
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Маппинг canisterId -> ingredient_code (базовый)
CANISTER_TO_INGREDIENT = {
    '0': 'WATER',  # Вода (будет создана)
    '2': 'CREAM_ALMAFOOD_TOPPING_SATURATO_1KG',  # Заменитель сливок (молоко)
    '3': 'CHOCOLATE_ARISTOCRAT_PREMIUM_1KG',  # Шоколад
    '170': 'COFFEE_ESPRESSO_BLEND_1_1KG',  # Кофе
}

# Маппинг названий рецептов -> ingredient_code для canisterId=1 (сыпучие ингредиенты)
RECIPE_NAME_TO_INGREDIENT_1 = {
    # РАФ кокосовый
    'РАФ кокосовый': 'RAF_ARISTOCRAT_COCONUT_1KG',
    'РАФ кокосовый 250 мл.': 'RAF_ARISTOCRAT_COCONUT_1KG',
    'РАФ кокосовый 350 мл.': 'RAF_ARISTOCRAT_COCONUT_1KG',
    
    # РАФ банановый
    'РАФ банановый': 'RAF_ARISTOCRAT_BANANA_1KG',
    'РАФ банановый 250 мл.': 'RAF_ARISTOCRAT_BANANA_1KG',
    'РАФ банановый 350 мл.': 'RAF_ARISTOCRAT_BANANA_1KG',
    
    # РАФ клубника банан
    'РАФ клубника банан': 'RAF_ARISTOCRAT_STRAWBERRY_BANANA_1KG',
    'РАФ клубника банан 350 мл.': 'RAF_ARISTOCRAT_STRAWBERRY_BANANA_1KG',
    
    # Молочные коктейли
    'Молочный коктейль с бананом': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
    'Молочный коктейль с бананом 250 мл.': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
    'Молочный коктейль с бананом 350 мл.': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
    
    'Молочный коктейль с кокосом': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
    'Молочный коктейль с кокосом 250 мл.': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
    'Молочный коктейль с кокосом 350 мл.': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
    
    'Молочный коктейль клубника банан': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
    'Молочный коктейль клубника банан 250 мл.': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
    'Молочный коктейль клубника банан 350 мл.': 'MILKSHAKE_ARISTOCRAT_COLD_1KG',
}


def create_water_ingredient(db_session) -> bool:
    """Создает ингредиент 'Вода' если его нет."""
    try:
        # Проверяем, существует ли уже
        result = db_session.execute(
            text("SELECT ingredient_code FROM ingredients WHERE ingredient_code = 'WATER'")
        )
        if result.fetchone():
            print("✓ Ингредиент 'Вода' уже существует")
            return True
        
        # Создаем ингредиент Вода
        db_session.execute(
            text("""
                INSERT INTO ingredients (
                    ingredient_code, display_name_ru, unit, unit_ru,
                    expense_kind, is_active, ingredient_group
                ) VALUES (
                    'WATER', 'Вода', 'ml', 'мл',
                    'not_tracked', true, 'Прочие сухие напитки'
                )
            """)
        )
        db_session.commit()
        print("✓ Создан ингредиент 'Вода' (WATER)")
        return True
    except Exception as e:
        db_session.rollback()
        print(f"✗ Ошибка при создании ингредиента 'Вода': {e}")
        return False


def get_ingredient_code_for_canister(canister_id: str, recipe_name: str) -> Optional[str]:
    """Определяет ingredient_code для canisterId."""
    if canister_id == '1':
        # Для canisterId=1 определяем по названию рецепта
        return RECIPE_NAME_TO_INGREDIENT_1.get(recipe_name)
    else:
        # Для остальных используем базовый маппинг
        return CANISTER_TO_INGREDIENT.get(canister_id)


def load_json_file(file_path: str) -> List[Dict]:
    """Загружает JSON файл."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ Ошибка загрузки файла {file_path}: {e}")
        sys.exit(1)


def get_unique_recipe_names(products: List[Dict], recipes: List[Dict]) -> List[str]:
    """Извлекает уникальные названия рецептов из обоих файлов."""
    recipe_names = set()
    
    # Из products
    for product in products:
        recipe_name = product.get('recipeName')
        if recipe_name:
            recipe_names.add(recipe_name)
    
    # Из recipes
    for recipe in recipes:
        recipe_name = recipe.get('recipeName')
        if recipe_name:
            recipe_names.add(recipe_name)
    
    return sorted(list(recipe_names))


def create_drinks(db_session, recipe_names: List[str], products: List[Dict]) -> Dict[str, int]:
    """Создает записи в drinks и возвращает маппинг name -> id."""
    name_to_id = {}
    created_count = 0
    skipped_count = 0
    
    for recipe_name in recipe_names:
        # Проверяем, существует ли уже
        result = db_session.execute(
            text("SELECT id FROM drinks WHERE name = :name"),
            {"name": recipe_name}
        )
        existing = result.fetchone()
        
        if existing:
            name_to_id[recipe_name] = existing[0]
            skipped_count += 1
            continue
        
        # Определяем is_active из products
        is_active = False
        for product in products:
            if product.get('recipeName') == recipe_name:
                visible = product.get('visible', False)
                enable = product.get('enable', False)
                is_active = visible and enable
                break
        
        # Создаем запись
        result = db_session.execute(
            text("""
                INSERT INTO drinks (name, is_active)
                VALUES (:name, :is_active)
                RETURNING id
            """),
            {"name": recipe_name, "is_active": is_active}
        )
        drink_id = result.fetchone()[0]
        name_to_id[recipe_name] = drink_id
        created_count += 1
    
    db_session.commit()
    print(f"✓ Создано напитков: {created_count}, пропущено (уже существует): {skipped_count}")
    return name_to_id


def create_drink_items(db_session, recipes: List[Dict], name_to_id: Dict[str, int]) -> Tuple[int, int]:
    """Создает записи в drink_items на основе stepses из recipes."""
    created_count = 0
    skipped_count = 0
    errors = []
    
    for recipe in recipes:
        recipe_name = recipe.get('recipeName')
        if not recipe_name:
            continue
        
        drink_id = name_to_id.get(recipe_name)
        if not drink_id:
            errors.append(f"Рецепт '{recipe_name}' не найден в drinks")
            continue
        
        steps = recipe.get('stepses', [])
        if not steps:
            continue
        
        # Удаляем старые записи для этого рецепта
        db_session.execute(
            text("DELETE FROM drink_items WHERE drink_id = :drink_id"),
            {"drink_id": drink_id}
        )
        
        # Собираем ингредиенты с суммированием количеств для одинаковых ингредиентов
        ingredients_map = {}  # {ingredient_code: {'qty': Decimal, 'unit': str}}
        
        # Суммируем всю воду из всех шагов (waterVolume)
        total_water_ml = Decimal('0')
        
        # Получаем prebrewingWaterRatio из esAttr (абсолютное значение в мл для предсмачивания)
        es_attr = recipe.get('esAttr', {})
        prebrewing_water_ratio = es_attr.get('prebrewingWaterRatio')
        prebrewing_water_ml = None
        
        if prebrewing_water_ratio:
            try:
                # prebrewingWaterRatio - это абсолютное значение в мл, а не процент
                prebrewing_water_ml = Decimal(str(prebrewing_water_ratio))
            except:
                pass
        
        # Создаем новые записи
        for step in steps:
            canister_id = str(step.get('canisterId', ''))
            if not canister_id:
                continue
            
            # Определяем ingredient_code
            ingredient_code = get_ingredient_code_for_canister(canister_id, recipe_name)
            if not ingredient_code:
                errors.append(
                    f"Не найден ingredient_code для canisterId={canister_id} "
                    f"в рецепте '{recipe_name}'"
                )
                continue
            
            # Определяем qty_per_unit и unit
            gradient_weight = step.get('gradientWeight')
            water_volume = step.get('waterVolume')
            
            # Суммируем всю воду из всех шагов (waterVolume присутствует во многих шагах)
            if water_volume:
                try:
                    total_water_ml += Decimal(str(water_volume))
                except:
                    pass
            
            if canister_id == '0':  # Вода (canisterId=0) - только суммируем в total_water_ml, не добавляем в ingredients_map
                # Вода из canisterId=0 уже учтена в total_water_ml выше
                continue
            elif canister_id == '170':  # Кофе - используем gradientWeight в г
                if gradient_weight:
                    qty_per_unit = Decimal(str(gradient_weight))
                    unit = 'g'
                else:
                    continue
            elif canister_id == '2':  # Молоко (заменитель сливок) - используем gradientWeight в г
                if gradient_weight:
                    qty_per_unit = Decimal(str(gradient_weight))
                    unit = 'g'
                else:
                    continue
            elif canister_id == '3':  # Шоколад - используем gradientWeight в г
                if gradient_weight:
                    qty_per_unit = Decimal(str(gradient_weight))
                    unit = 'g'
                else:
                    continue
            elif canister_id == '1':  # Сыпучие ингредиенты - используем gradientWeight в г
                if gradient_weight:
                    qty_per_unit = Decimal(str(gradient_weight))
                    unit = 'g'
                else:
                    continue
            else:
                # По умолчанию используем gradientWeight если есть, иначе waterVolume
                if gradient_weight:
                    qty_per_unit = Decimal(str(gradient_weight))
                    unit = 'g'
                elif water_volume:
                    qty_per_unit = Decimal(str(water_volume))
                    unit = 'ml'
                else:
                    continue
            
            # Проверяем, существует ли ингредиент
            result = db_session.execute(
                text("SELECT ingredient_code FROM ingredients WHERE ingredient_code = :code"),
                {"code": ingredient_code}
            )
            if not result.fetchone():
                errors.append(
                    f"Ингредиент '{ingredient_code}' не найден в базе "
                    f"(рецепт: '{recipe_name}', canisterId: {canister_id})"
                )
                continue
            
            # Суммируем количества для одинаковых ингредиентов
            if ingredient_code in ingredients_map:
                # Проверяем, что единицы измерения совпадают
                if ingredients_map[ingredient_code]['unit'] == unit:
                    ingredients_map[ingredient_code]['qty'] += qty_per_unit
                else:
                    errors.append(
                        f"Конфликт единиц измерения для '{ingredient_code}' "
                        f"в рецепте '{recipe_name}': {ingredients_map[ingredient_code]['unit']} vs {unit}"
                    )
            else:
                ingredients_map[ingredient_code] = {
                    'qty': qty_per_unit,
                    'unit': unit
                }
        
        # Добавляем prebrewingWaterRatio как абсолютное значение в мл (один раз для всего рецепта)
        if prebrewing_water_ml is not None:
            total_water_ml += prebrewing_water_ml
        
        # Добавляем воду, если она есть (суммированная из всех шагов + предсмачивание)
        if total_water_ml > 0:
            # Проверяем, не добавлена ли уже вода из canisterId=0
            if 'WATER' not in ingredients_map:
                # Проверяем, существует ли ингредиент WATER
                result = db_session.execute(
                    text("SELECT ingredient_code FROM ingredients WHERE ingredient_code = 'WATER'")
                )
                if result.fetchone():
                    ingredients_map['WATER'] = {
                        'qty': total_water_ml,
                        'unit': 'ml'
                    }
                else:
                    errors.append(
                        f"Ингредиент 'WATER' не найден в базе (рецепт: '{recipe_name}')"
                    )
            else:
                # Если вода уже есть из canisterId=0, суммируем
                ingredients_map['WATER']['qty'] += total_water_ml
        
        # Создаем записи в drink_items из собранного словаря
        for ingredient_code, data in ingredients_map.items():
            db_session.execute(
                text("""
                    INSERT INTO drink_items (drink_id, ingredient_code, qty_per_unit, unit)
                    VALUES (:drink_id, :ingredient_code, :qty, :unit)
                """),
                {
                    "drink_id": drink_id,
                    "ingredient_code": ingredient_code,
                    "qty": data['qty'],
                    "unit": data['unit']
                }
            )
            created_count += 1
    
    db_session.commit()
    
    if errors:
        print(f"\n⚠ Предупреждения ({len(errors)}):")
        for error in errors[:10]:  # Показываем первые 10
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... и еще {len(errors) - 10} предупреждений")
    
    print(f"✓ Создано записей в drink_items: {created_count}, обновлено: {skipped_count}")
    return created_count, skipped_count


def main():
    parser = argparse.ArgumentParser(description='Импорт рецептов из JSON файлов')
    parser.add_argument('--product-file', required=True, help='Путь к product.json')
    parser.add_argument('--recipe-file', required=True, help='Путь к recipe.json')
    parser.add_argument('--dry-run', action='store_true', help='Проверка без сохранения в БД')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ИМПОРТ РЕЦЕПТОВ ИЗ JSON ФАЙЛОВ")
    print("=" * 80)
    print(f"Product file: {args.product_file}")
    print(f"Recipe file: {args.recipe_file}")
    if args.dry_run:
        print("⚠ DRY RUN MODE - изменения не будут сохранены")
    print()
    
    # Загружаем файлы
    print("📂 Загрузка JSON файлов...")
    products = load_json_file(args.product_file)
    recipes = load_json_file(args.recipe_file)
    print(f"✓ Загружено продуктов: {len(products)}")
    print(f"✓ Загружено рецептов: {len(recipes)}")
    print()
    
    # Подключаемся к БД
    if not args.dry_run:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        
        try:
            # Создаем ингредиент "Вода"
            print("💧 Создание ингредиента 'Вода'...")
            create_water_ingredient(db_session)
            print()
            
            # Извлекаем уникальные названия рецептов
            print("📋 Извлечение уникальных названий рецептов...")
            recipe_names = get_unique_recipe_names(products, recipes)
            print(f"✓ Найдено уникальных рецептов: {len(recipe_names)}")
            print()
            
            # Создаем записи в drinks
            print("🍹 Создание записей в drinks...")
            name_to_id = create_drinks(db_session, recipe_names, products)
            print()
            
            # Создаем записи в drink_items
            print("📝 Создание записей в drink_items...")
            create_drink_items(db_session, recipes, name_to_id)
            print()
            
            print("=" * 80)
            print("✅ ИМПОРТ ЗАВЕРШЕН УСПЕШНО")
            print("=" * 80)
            
        except Exception as e:
            db_session.rollback()
            print(f"\n✗ Ошибка при импорте: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            db_session.close()
    else:
        print("⚠ DRY RUN MODE - пропущено сохранение в БД")
        print("\nБыло бы создано:")
        recipe_names = get_unique_recipe_names(products, recipes)
        print(f"  - Напитков: {len(recipe_names)}")
        print(f"  - Записей в drink_items: (требуется анализ stepses)")


if __name__ == '__main__':
    main()
