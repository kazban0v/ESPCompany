#!/usr/bin/env python
"""
Скрипт для запуска миграции данных из SQLite в PostgreSQL на Railway
Использование:
    railway run python run_migration.py
"""
import os
import sys

# Проверяем наличие DATABASE_URL
if not os.environ.get('DATABASE_URL'):
    print("=" * 60)
    print("❌ ОШИБКА: DATABASE_URL не установлен!")
    print("=" * 60)
    print("\nДля создания PostgreSQL базы данных:")
    print("1. Откройте https://railway.app")
    print("2. Войдите в проект 'insightful-vitality'")
    print("3. Нажмите '+ New' → 'Database' → 'Add PostgreSQL'")
    print("4. Railway автоматически добавит переменную DATABASE_URL")
    print("5. Запустите этот скрипт снова: railway run python run_migration.py")
    sys.exit(1)

# Импортируем и запускаем скрипт миграции
from migrate_sqlite_to_postgres import migrate_data

if __name__ == '__main__':
    success = migrate_data()
    sys.exit(0 if success else 1)

