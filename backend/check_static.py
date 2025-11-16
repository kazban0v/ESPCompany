#!/usr/bin/env python
"""
Скрипт для проверки статических файлов на Railway
Проверяет, что файлы собраны и доступны
"""
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esp_site.settings')

import django
django.setup()

from django.conf import settings
from django.core.management import call_command

# Проверяем директорию staticfiles
staticfiles_dir = BASE_DIR / 'staticfiles'
print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
print(f"staticfiles_dir exists: {staticfiles_dir.exists()}")

if staticfiles_dir.exists():
    # Считаем файлы
    css_files = list(staticfiles_dir.rglob('*.css'))
    js_files = list(staticfiles_dir.rglob('*.js'))
    img_files = list(staticfiles_dir.rglob('*.png')) + list(staticfiles_dir.rglob('*.jpg'))
    
    print(f"CSS files: {len(css_files)}")
    print(f"JS files: {len(js_files)}")
    print(f"Image files: {len(img_files)}")
    
    # Проверяем конкретные файлы
    main_js = staticfiles_dir / 'js' / 'main.js'
    custom_css = staticfiles_dir / 'css' / 'custom.css'
    
    print(f"main.js exists: {main_js.exists()}")
    print(f"custom.css exists: {custom_css.exists()}")
    
    if not main_js.exists() or not custom_css.exists():
        print("⚠ Статические файлы не найдены, выполняем collectstatic...")
        call_command('collectstatic', '--noinput', verbosity=2)
        print("✓ collectstatic выполнен")
else:
    print("⚠ Директория staticfiles не существует, создаем и собираем файлы...")
    staticfiles_dir.mkdir(exist_ok=True)
    call_command('collectstatic', '--noinput', verbosity=2)
    print("✓ collectstatic выполнен")

print("✓ Проверка статических файлов завершена")

