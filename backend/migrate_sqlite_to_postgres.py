#!/usr/bin/env python
"""
Скрипт для миграции данных из SQLite в PostgreSQL
Использование:
    python migrate_sqlite_to_postgres.py
"""
import os
import sys
from pathlib import Path
import django

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esp_site.settings')
django.setup()

from django.conf import settings
from django.db import connections
from catalog.models import Category, Subcategory, Section, Product


def migrate_data():
    """
    Мигрирует данные из SQLite в PostgreSQL
    """
    print("=" * 60)
    print("МИГРАЦИЯ ДАННЫХ ИЗ SQLITE В POSTGRESQL")
    print("=" * 60)
    
    # Проверяем наличие SQLite базы данных
    # Пробуем несколько возможных путей
    sqlite_db = None
    possible_paths = [
        BASE_DIR / 'db.sqlite3',
        Path(r'C:\Users\User\Desktop\ESPCompany\backend\db.sqlite3'),
        Path(__file__).parent.parent / 'backend' / 'db.sqlite3',
        Path('/app/db.sqlite3'),  # Путь на Railway
    ]
    
    for path in possible_paths:
        if path.exists():
            sqlite_db = path
            break
    
    if not sqlite_db or not sqlite_db.exists():
        print(f"❌ SQLite база данных не найдена!")
        print("Проверенные пути:")
        for path in possible_paths:
            print(f"  - {path} ({'существует' if path.exists() else 'не найден'})")
        print("\n⚠ ВНИМАНИЕ: Если вы запускаете миграцию на Railway,")
        print("   SQLite база данных должна быть загружена в проект.")
        print("   Или используйте локальную SQLite базу для экспорта данных.")
        return False
    
    print(f"✓ SQLite база данных найдена: {sqlite_db}")
    
    # Проверяем настройки базы данных
    current_db = settings.DATABASES['default']
    print(f"\nТекущая база данных: {current_db['ENGINE']}")
    
    # Если используется SQLite, нужно временно переключиться на PostgreSQL
    if 'sqlite3' in current_db['ENGINE']:
        print("\n⚠ ВНИМАНИЕ: Сейчас используется SQLite!")
        print("Для миграции нужно:")
        print("1. Создать PostgreSQL базу данных в Railway")
        print("2. Установить переменную окружения DATABASE_URL")
        print("3. Запустить этот скрипт снова")
        return False
    
    if 'postgresql' not in current_db['ENGINE']:
        print(f"❌ Неподдерживаемая база данных: {current_db['ENGINE']}")
        return False
    
    print("✓ Используется PostgreSQL")
    
    # Подключаемся к SQLite для чтения данных
    print("\n" + "=" * 60)
    print("ШАГ 1: Чтение данных из SQLite")
    print("=" * 60)
    
    # Добавляем SQLite как дополнительную базу данных
    # Используем полную конфигурацию из settings для совместимости
    from django.conf import settings as django_settings
    sqlite_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(sqlite_db),
        'TIME_ZONE': django_settings.TIME_ZONE,
        'OPTIONS': {},
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
    }
    
    # Добавляем SQLite базу данных в настройки
    settings.DATABASES['sqlite'] = sqlite_config
    connections.databases['sqlite'] = sqlite_config
    
    try:
        # Читаем данные из SQLite
        print("\nЧтение категорий...")
        categories = list(Category.objects.using('sqlite').all())
        print(f"✓ Найдено категорий: {len(categories)}")
        
        print("\nЧтение подкатегорий...")
        subcategories = list(Subcategory.objects.using('sqlite').all())
        print(f"✓ Найдено подкатегорий: {len(subcategories)}")
        
        print("\nЧтение разделов...")
        sections = list(Section.objects.using('sqlite').all())
        print(f"✓ Найдено разделов: {len(sections)}")
        
        print("\nЧтение товаров...")
        products = list(Product.objects.using('sqlite').all())
        print(f"✓ Найдено товаров: {len(products)}")
        
    except Exception as e:
        print(f"❌ Ошибка при чтении из SQLite: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Записываем данные в PostgreSQL
    print("\n" + "=" * 60)
    print("ШАГ 2: Запись данных в PostgreSQL")
    print("=" * 60)
    
    try:
        # Мигрируем категории
        print("\nМиграция категорий...")
        category_map = {}  # Старый ID -> Новый объект
        for cat in categories:
            # Проверяем, существует ли уже такая категория
            existing = Category.objects.filter(slug=cat.slug).first()
            if existing:
                print(f"  ⚠ Категория '{cat.title}' уже существует, пропускаем")
                category_map[cat.id] = existing
            else:
                new_cat = Category(
                    title=cat.title,
                    slug=cat.slug,
                    description=cat.description,
                    is_active=cat.is_active,
                    order=cat.order,
                    created_at=cat.created_at,
                    updated_at=cat.updated_at,
                )
                new_cat.save()
                category_map[cat.id] = new_cat
                print(f"  ✓ Категория '{cat.title}' мигрирована")
        
        # Мигрируем подкатегории
        print("\nМиграция подкатегорий...")
        subcategory_map = {}  # Старый ID -> Новый объект
        for subcat in subcategories:
            # Проверяем, существует ли уже такая подкатегория
            existing = Subcategory.objects.filter(
                category=category_map[subcat.category_id],
                slug=subcat.slug
            ).first()
            if existing:
                print(f"  ⚠ Подкатегория '{subcat.title}' уже существует, пропускаем")
                subcategory_map[subcat.id] = existing
            else:
                new_subcat = Subcategory(
                    category=category_map[subcat.category_id],
                    title=subcat.title,
                    slug=subcat.slug,
                    description=subcat.description,
                    is_active=subcat.is_active,
                    order=subcat.order,
                    created_at=subcat.created_at,
                    updated_at=subcat.updated_at,
                )
                new_subcat.save()
                subcategory_map[subcat.id] = new_subcat
                print(f"  ✓ Подкатегория '{subcat.title}' мигрирована")
        
        # Мигрируем разделы
        print("\nМиграция разделов...")
        section_map = {}  # Старый ID -> Новый объект
        for section in sections:
            # Проверяем, существует ли уже такой раздел
            existing = Section.objects.filter(
                subcategory=subcategory_map[section.subcategory_id],
                slug=section.slug
            ).first()
            if existing:
                print(f"  ⚠ Раздел '{section.title}' уже существует, пропускаем")
                section_map[section.id] = existing
            else:
                new_section = Section(
                    subcategory=subcategory_map[section.subcategory_id],
                    title=section.title,
                    slug=section.slug,
                    description=section.description,
                    is_active=section.is_active,
                    order=section.order,
                    created_at=section.created_at,
                    updated_at=section.updated_at,
                )
                new_section.save()
                section_map[section.id] = new_section
                print(f"  ✓ Раздел '{section.title}' мигрирована")
        
        # Мигрируем товары
        print("\nМиграция товаров...")
        migrated_count = 0
        skipped_count = 0
        for product in products:
            # Проверяем, существует ли уже такой товар
            existing = Product.objects.filter(sku=product.sku).first()
            if existing:
                print(f"  ⚠ Товар '{product.title}' (SKU: {product.sku}) уже существует, пропускаем")
                skipped_count += 1
                continue
            
            new_product = Product(
                section=section_map.get(product.section_id) if product.section_id else None,
                title=product.title,
                slug=product.slug,
                sku=product.sku,
                short_description=product.short_description,
                full_description=product.full_description,
                price=product.price,
                stock=product.stock,
                image=product.image,
                is_active=product.is_active,
                unit=product.unit,
                price_special=product.price_special,
                price_retail=product.price_retail,
                wire_section=product.wire_section,
                load_limit=product.load_limit,
                image_code=product.image_code,
                order=product.order,
                created_at=product.created_at,
                updated_at=product.updated_at,
            )
            new_product.save()
            migrated_count += 1
            if migrated_count % 10 == 0:
                print(f"  ✓ Мигрировано товаров: {migrated_count}")
        
        print(f"\n✓ Миграция завершена!")
        print(f"  - Категорий: {len(category_map)}")
        print(f"  - Подкатегорий: {len(subcategory_map)}")
        print(f"  - Разделов: {len(section_map)}")
        print(f"  - Товаров: {migrated_count} мигрировано, {skipped_count} пропущено")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при записи в PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = migrate_data()
    if success:
        print("\n" + "=" * 60)
        print("✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ МИГРАЦИЯ ЗАВЕРШИЛАСЬ С ОШИБКАМИ")
        print("=" * 60)
        sys.exit(1)

