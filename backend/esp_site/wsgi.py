"""
WSGI config for esp_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esp_site.settings')

# Создаем директорию staticfiles если её нет (для Railway)
BASE_DIR = Path(__file__).resolve().parent.parent
staticfiles_dir = BASE_DIR / 'staticfiles'
staticfiles_dir.mkdir(exist_ok=True)

# Применяем миграции если таблиц нет (для Railway SQLite)
try:
    application = get_wsgi_application()
    from django.db import connection
    cursor = connection.cursor()
    # Проверяем наличие таблицы catalog_product
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='catalog_product'")
    if not cursor.fetchone():
        # Таблиц нет, применяем миграции
        from django.core.management import call_command
        call_command('migrate', verbosity=0, interactive=False)
except Exception as e:
    # Если ошибка, просто продолжаем - миграции должны выполняться в startCommand
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not check/apply migrations in wsgi: {e}")
    application = get_wsgi_application()
