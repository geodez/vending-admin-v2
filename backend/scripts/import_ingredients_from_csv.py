#!/usr/bin/env python3
"""
Скрипт для импорта ингредиентов из CSV файла в базу данных.
Использование: python scripts/import_ingredients_from_csv.py <path_to_csv>
"""
import sys
import csv
from pathlib import Path
from decimal import Decimal

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.business import Ingredient
from sqlalchemy.exc import IntegrityError

def import_ingredients_from_csv(csv_path: str):
    """Импортирует ингредиенты из CSV файла в базу данных."""
    db = SessionLocal()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, quotechar='"', skipinitialspace=True)
            
            imported = 0
            skipped = 0
            errors = []
            
            for row in reader:
                try:
                    # Проверяем, существует ли уже ингредиент с таким кодом
                    existing = db.query(Ingredient).filter(
                        Ingredient.ingredient_code == row['ingredient_code']
                    ).first()
                    
                    if existing:
                        print(f"⚠️  Пропущен (уже существует): {row['ingredient_code']} - {row['display_name_ru']}")
                        skipped += 1
                        continue
                    
                    # Обрабатываем цену - убираем пробелы и проверяем на пустоту
                    cost_value = None
                    if row.get('cost_per_unit_rub') and row['cost_per_unit_rub'].strip():
                        try:
                            # Убираем пробелы и заменяем запятую на точку
                            cost_str = row['cost_per_unit_rub'].strip().replace(',', '.').replace(' ', '')
                            cost_value = Decimal(cost_str) if cost_str else None
                        except (ValueError, Exception):
                            cost_value = None
                    
                    # Создаем новый ингредиент
                    ingredient = Ingredient(
                        ingredient_code=row['ingredient_code'],
                        display_name_ru=row['display_name_ru'] if row.get('display_name_ru') and row['display_name_ru'].strip() else None,
                        ingredient_group=row['ingredient_group'] if row.get('ingredient_group') and row['ingredient_group'].strip() else None,
                        brand_name=row['brand_name'] if row.get('brand_name') and row['brand_name'].strip() else None,
                        unit=row['unit'],
                        unit_ru=row['unit_ru'] if row.get('unit_ru') and row['unit_ru'].strip() else None,
                        cost_per_unit_rub=cost_value,
                        expense_kind=row['expense_kind'] if row.get('expense_kind') and row['expense_kind'].strip() else 'stock_tracked',
                        is_active=row['is_active'].lower() == 'true' if row.get('is_active') and row['is_active'].strip() else True,
                    )
                    
                    db.add(ingredient)
                    db.commit()
                    
                    print(f"✅ Импортирован: {row['ingredient_code']} - {row['display_name_ru']}")
                    imported += 1
                    
                except IntegrityError as e:
                    db.rollback()
                    print(f"❌ Ошибка целостности для {row['ingredient_code']}: {e}")
                    errors.append((row['ingredient_code'], str(e)))
                    skipped += 1
                except Exception as e:
                    db.rollback()
                    print(f"❌ Ошибка для {row['ingredient_code']}: {e}")
                    errors.append((row['ingredient_code'], str(e)))
                    skipped += 1
        
        print(f"\n📊 Итоги импорта:")
        print(f"   ✅ Импортировано: {imported}")
        print(f"   ⚠️  Пропущено: {skipped}")
        if errors:
            print(f"   ❌ Ошибок: {len(errors)}")
            for code, error in errors:
                print(f"      - {code}: {error}")
        
    except FileNotFoundError:
        print(f"❌ Файл не найден: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python scripts/import_ingredients_from_csv.py <path_to_csv>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    import_ingredients_from_csv(csv_path)
