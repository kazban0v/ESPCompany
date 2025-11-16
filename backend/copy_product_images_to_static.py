#!/usr/bin/env python
"""
Скрипт для копирования изображений товаров из media/products в static/img/products
Использование:
    python copy_product_images_to_static.py
"""
import os
import sys
import shutil
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esp_site.settings')

import django
django.setup()

from catalog.models import Product

print("=" * 60)
print("КОПИРОВАНИЕ ИЗОБРАЖЕНИЙ ТОВАРОВ В STATIC")
print("=" * 60)

media_products_dir = BASE_DIR / 'media' / 'products'
static_products_dir = BASE_DIR / 'static' / 'img' / 'products'

# Создаем директорию static/img/products если её нет
static_products_dir.mkdir(parents=True, exist_ok=True)
print(f"✓ Директория создана: {static_products_dir}")

# Проверяем наличие media/products
if not media_products_dir.exists():
    print(f"⚠ Папка {media_products_dir} не найдена")
    print("Попробуем скопировать из базы данных...")
    
    # Получаем все товары с изображениями
    products = Product.objects.exclude(image='').exclude(image__isnull=True)
    print(f"Найдено товаров с изображениями: {products.count()}")
    
    copied = 0
    for product in products:
        if product.image:
            image_name = os.path.basename(product.image.name)
            # Пробуем найти файл в разных местах
            possible_paths = [
                BASE_DIR / 'media' / 'products' / image_name,
                BASE_DIR / 'static' / 'img' / 'linejnaya-armatura-ot-04-10-kv' / image_name,
                BASE_DIR / 'static' / 'img' / 'elektrotehnicheskij-zavod-kvt' / image_name,
            ]
            
            found = False
            for src_path in possible_paths:
                if src_path.exists():
                    dst_path = static_products_dir / image_name
                    if not dst_path.exists():
                        shutil.copy2(src_path, dst_path)
                        copied += 1
                        print(f"  ✓ Скопировано: {image_name}")
                    found = True
                    break
            
            if not found:
                print(f"  ✗ Не найдено: {image_name}")
    
    print(f"\n✓ Скопировано изображений: {copied}")
else:
    # Копируем все файлы из media/products в static/img/products
    print(f"Копируем из {media_products_dir} в {static_products_dir}...")
    
    copied = 0
    skipped = 0
    
    for file_path in media_products_dir.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(media_products_dir)
            dst_path = static_products_dir / relative_path
            
            # Создаем поддиректории если нужно
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not dst_path.exists():
                shutil.copy2(file_path, dst_path)
                copied += 1
            else:
                skipped += 1
    
    print(f"✓ Скопировано: {copied}, пропущено (уже есть): {skipped}")

# Проверяем результат
if static_products_dir.exists():
    image_files = list(static_products_dir.rglob('*.jpg')) + list(static_products_dir.rglob('*.png')) + list(static_products_dir.rglob('*.jpeg'))
    print(f"\n✓ Всего изображений в static/img/products: {len(image_files)}")

print("=" * 60)
print("ГОТОВО!")
print("=" * 60)


