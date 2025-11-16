#!/usr/bin/env python
"""
Скрипт для проверки статических файлов на Railway
Проверяет, что файлы собраны и доступны
"""
import os
import sys
from pathlib import Path

print("=" * 50)
print("CHECK_STATIC.PY: Начало проверки статических файлов")
print("=" * 50)

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
print(f"BASE_DIR: {BASE_DIR}")
print(f"staticfiles_dir path: {staticfiles_dir}")
print(f"staticfiles_dir exists: {staticfiles_dir.exists()}")

# Всегда выполняем collectstatic для надежности
print("\nВыполняем collectstatic...")
try:
    # Сначала очищаем старые файлы
    if staticfiles_dir.exists():
        import shutil
        shutil.rmtree(staticfiles_dir)
        print("✓ Старая директория staticfiles удалена")
    
    # Создаем новую директорию
    staticfiles_dir.mkdir(exist_ok=True)
    print("✓ Директория staticfiles создана")
    
    # Выполняем collectstatic
    result = call_command('collectstatic', '--noinput', '--clear', verbosity=2)
    print("✓ collectstatic выполнен успешно")
except Exception as e:
    print(f"✗ Ошибка при collectstatic: {e}")
    import traceback
    traceback.print_exc()

# Проверяем результат
if staticfiles_dir.exists():
    # Считаем файлы
    css_files = list(staticfiles_dir.rglob('*.css'))
    js_files = list(staticfiles_dir.rglob('*.js'))
    img_files = list(staticfiles_dir.rglob('*.png')) + list(staticfiles_dir.rglob('*.jpg'))
    
    print(f"\nРезультаты:")
    print(f"CSS files: {len(css_files)}")
    print(f"JS files: {len(js_files)}")
    print(f"Image files: {len(img_files)}")
    
    # Проверяем конкретные файлы
    main_js = staticfiles_dir / 'js' / 'main.js'
    custom_css = staticfiles_dir / 'css' / 'custom.css'
    
    print(f"\nПроверка конкретных файлов:")
    print(f"main.js exists: {main_js.exists()} (path: {main_js})")
    print(f"custom.css exists: {custom_css.exists()} (path: {custom_css})")
    
    if main_js.exists():
        print(f"main.js size: {main_js.stat().st_size} bytes")
    if custom_css.exists():
        print(f"custom.css size: {custom_css.stat().st_size} bytes")
else:
    print("✗ Директория staticfiles не существует после collectstatic!")

print("=" * 50)
print("CHECK_STATIC.PY: Проверка завершена")
print("=" * 50)

