#!/usr/bin/env python3
"""Скрипт для поиска стаканов и крышек в базе данных."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text("""
        SELECT ingredient_code, display_name_ru 
        FROM ingredients 
        WHERE LOWER(display_name_ru) LIKE '%стакан%' 
           OR LOWER(display_name_ru) LIKE '%крыш%'
           OR LOWER(ingredient_code) LIKE '%cup%'
           OR LOWER(ingredient_code) LIKE '%lid%'
        ORDER BY display_name_ru
    """))
    rows = result.fetchall()
    if rows:
        print("Найденные ингредиенты:")
        for row in rows:
            print(f"  {row[0]}: {row[1]}")
    else:
        print("Не найдено ингредиентов со стаканами или крышками")
finally:
    db.close()
