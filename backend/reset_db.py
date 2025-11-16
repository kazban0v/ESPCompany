#!/usr/bin/env python
"""
Скрипт для сброса базы данных на Railway
Удаляет базу данных и применяет миграции заново
"""
import os
import sys
from pathlib import Path

print("=" * 50)
print("RESET_DB.PY: Начало работы")
print("=" * 50)

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esp_site.settings')

import django
django.setup()

from django.db import connection
from django.core.management import call_command

# Проверяем наличие базы данных
db_path = BASE_DIR / 'db.sqlite3'
print(f"База данных: {db_path}")
print(f"База данных существует: {db_path.exists()}")

# Проверяем, существует ли база данных
if db_path.exists():
    try:
        # Пытаемся применить миграции
        call_command('migrate', verbosity=2, interactive=False)
        print("✓ Миграции применены успешно")
    except Exception as e:
        print(f"✗ Ошибка при применении миграций: {e}")
        print("Попытка пересоздать базу данных...")
        
        # Удаляем базу данных
        db_path.unlink()
        print("✓ Старая база данных удалена")
        
        # Применяем миграции заново
        try:
            call_command('migrate', verbosity=2, interactive=False)
            print("✓ База данных пересоздана, миграции применены")
        except Exception as e2:
            print(f"✗ Критическая ошибка: {e2}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
else:
    # Базы данных нет, создаем её
    print("База данных не найдена, создаем новую...")
    try:
        call_command('migrate', verbosity=2, interactive=False)
        print("✓ База данных создана, миграции применены")
    except Exception as e:
        print(f"✗ Ошибка при создании базы данных: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("✓ База данных готова")

# Проверяем, что таблицы созданы
cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='catalog_product'")
if cursor.fetchone():
    print("✓ Таблица catalog_product существует")
else:
    print("✗ Таблица catalog_product не найдена")

