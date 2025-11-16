from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Category, Subcategory, Section, Product, Order, OrderItem, Lead


# Inline для подкатегорий
class SubcategoryInline(admin.TabularInline):
    """Inline для создания и редактирования подкатегорий"""
    model = Subcategory
    extra = 3
    fields = ('title', 'slug', 'order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}


# Inline для разделов
class SectionInline(admin.TabularInline):
    """Inline для создания и редактирования разделов"""
    model = Section
    extra = 3
    fields = ('title', 'slug', 'order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}


# Inline для товаров
class ProductInline(admin.TabularInline):
    """Inline для создания и редактирования товаров"""
    model = Product
    extra = 3
    fields = ('title', 'slug', 'sku', 'price', 'price_special', 'price_retail', 'image', 'order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий (первый уровень)"""
    list_display = ('title', 'order', 'is_active', 'subcategories_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')
    list_editable = ('order', 'is_active')
    actions = ['make_active', 'make_inactive', 'delete_selected_categories']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'order', 'is_active'),
        }),
    )
    inlines = [SubcategoryInline]
    
    def get_queryset(self, request):
        """Оптимизация запросов для отображения"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('subcategories')
    
    def delete_model(self, request, obj):
        """Удаление одной категории с проверкой связанных объектов"""
        try:
            subcategories_count = obj.subcategories.count()
            if subcategories_count > 0:
                self.message_user(
                    request,
                    f'Нельзя удалить категорию "{obj.title}": у неё есть {subcategories_count} подкатегорий. '
                    f'Сначала удалите или переместите подкатегории.',
                    level='ERROR'
                )
                return
            
            obj.delete()
            self.message_user(request, f'Категория "{obj.title}" успешно удалена.')
        except Exception as e:
            self.message_user(request, f'Ошибка при удалении категории: {str(e)}', level='ERROR')
    
    def delete_selected_categories(self, request, queryset):
        """Массовое удаление категорий с проверкой"""
        deleted = 0
        errors = []
        
        for category in queryset:
            try:
                subcategories_count = category.subcategories.count()
                if subcategories_count > 0:
                    errors.append(f'"{category.title}": есть {subcategories_count} подкатегорий')
                    continue
                
                category.delete()
                deleted += 1
            except Exception as e:
                errors.append(f'"{category.title}": {str(e)}')
        
        if deleted > 0:
            self.message_user(request, f'Удалено категорий: {deleted}')
        if errors:
            self.message_user(
                request,
                f'Не удалось удалить {len(errors)} категорий:\n' + '\n'.join(errors),
                level='ERROR'
            )
    delete_selected_categories.short_description = 'Удалить выбранные категории'

    def make_active(self, request, queryset):
        """Массовое действие: сделать категории активными"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано категорий: {updated}')
    make_active.short_description = 'Активировать выбранные категории'

    def make_inactive(self, request, queryset):
        """Массовое действие: сделать категории неактивными"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано категорий: {updated}')
    make_inactive.short_description = 'Деактивировать выбранные категории'

    def subcategories_count(self, obj):
        """Количество подкатегорий"""
        count = obj.subcategories.count()
        if count > 0:
            url = reverse('admin:catalog_subcategory_changelist') + f'?category__id__exact={obj.pk}'
            return format_html('<a href="{}">{} подкатегорий</a>', url, count)
        return '0 подкатегорий'
    subcategories_count.short_description = 'Подкатегорий'


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    """Админка для подкатегорий (второй уровень)"""
    list_display = ('title', 'category_link', 'order', 'is_active', 'sections_count', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description', 'category__title')
    list_editable = ('order', 'is_active')
    autocomplete_fields = ['category']
    actions = ['make_active', 'make_inactive', 'delete_selected_subcategories']
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'title', 'slug', 'description', 'order', 'is_active'),
        }),
    )
    inlines = [SectionInline]
    
    def get_queryset(self, request):
        """Оптимизация запросов для отображения"""
        qs = super().get_queryset(request)
        return qs.select_related('category').prefetch_related('sections')
    
    def delete_model(self, request, obj):
        """Удаление одной подкатегории с проверкой связанных объектов"""
        try:
            sections_count = obj.sections.count()
            if sections_count > 0:
                self.message_user(
                    request,
                    f'Нельзя удалить подкатегорию "{obj.title}": у неё есть {sections_count} разделов. '
                    f'Сначала удалите или переместите разделы.',
                    level='ERROR'
                )
                return
            
            obj.delete()
            self.message_user(request, f'Подкатегория "{obj.title}" успешно удалена.')
        except Exception as e:
            self.message_user(request, f'Ошибка при удалении подкатегории: {str(e)}', level='ERROR')
    
    def delete_selected_subcategories(self, request, queryset):
        """Массовое удаление подкатегорий с проверкой"""
        deleted = 0
        errors = []
        
        for subcategory in queryset:
            try:
                sections_count = subcategory.sections.count()
                if sections_count > 0:
                    errors.append(f'"{subcategory.title}": есть {sections_count} разделов')
                    continue
                
                subcategory.delete()
                deleted += 1
            except Exception as e:
                errors.append(f'"{subcategory.title}": {str(e)}')
        
        if deleted > 0:
            self.message_user(request, f'Удалено подкатегорий: {deleted}')
        if errors:
            self.message_user(
                request,
                f'Не удалось удалить {len(errors)} подкатегорий:\n' + '\n'.join(errors),
                level='ERROR'
            )
    delete_selected_subcategories.short_description = 'Удалить выбранные подкатегории'

    def make_active(self, request, queryset):
        """Массовое действие: сделать подкатегории активными"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано подкатегорий: {updated}')
    make_active.short_description = 'Активировать выбранные подкатегории'

    def make_inactive(self, request, queryset):
        """Массовое действие: сделать подкатегории неактивными"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано подкатегорий: {updated}')
    make_inactive.short_description = 'Деактивировать выбранные подкатегории'

    def category_link(self, obj):
        """Ссылка на категорию"""
        if obj.category:
            url = reverse('admin:catalog_category_change', args=[obj.category.pk])
            return format_html('<a href="{}">{}</a>', url, obj.category.title)
        return '-'
    category_link.short_description = 'Категория'

    def sections_count(self, obj):
        """Количество разделов"""
        count = obj.sections.count()
        if count > 0:
            url = reverse('admin:catalog_section_changelist') + f'?subcategory__id__exact={obj.pk}'
            return format_html('<a href="{}">{} разделов</a>', url, count)
        return '0 разделов'
    sections_count.short_description = 'Разделов'


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    """Админка для разделов (третий уровень)"""
    list_display = ('title', 'subcategory_link', 'order', 'is_active', 'products_count', 'created_at')
    list_filter = ('is_active', 'subcategory__category', 'subcategory', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description', 'subcategory__title', 'subcategory__category__title')
    list_editable = ('order', 'is_active')
    autocomplete_fields = ['subcategory']
    actions = ['make_active', 'make_inactive', 'delete_selected_sections']
    fieldsets = (
        ('Основная информация', {
            'fields': ('subcategory', 'title', 'slug', 'description', 'order', 'is_active'),
        }),
    )
    
    def get_queryset(self, request):
        """Оптимизация запросов для отображения"""
        qs = super().get_queryset(request)
        return qs.select_related('subcategory__category').prefetch_related('products')
    
    def delete_selected_sections(self, request, queryset):
        """Массовое удаление разделов"""
        deleted = queryset.count()
        queryset.delete()
        self.message_user(request, f'Удалено разделов: {deleted}')
    delete_selected_sections.short_description = 'Удалить выбранные разделы'

    def make_active(self, request, queryset):
        """Массовое действие: сделать разделы активными"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано разделов: {updated}')
    make_active.short_description = 'Активировать выбранные разделы'

    def make_inactive(self, request, queryset):
        """Массовое действие: сделать разделы неактивными"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано разделов: {updated}')
    make_inactive.short_description = 'Деактивировать выбранные разделы'

    def subcategory_link(self, obj):
        """Ссылка на подкатегорию"""
        if obj.subcategory:
            url = reverse('admin:catalog_subcategory_change', args=[obj.subcategory.pk])
            return format_html('<a href="{}">{}</a>', url, str(obj.subcategory))
        return '-'
    subcategory_link.short_description = 'Подкатегория'

    def products_count(self, obj):
        """Количество товаров в разделе"""
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:catalog_product_changelist') + f'?section__id__exact={obj.pk}'
            return format_html('<a href="{}">{} товаров</a>', url, count)
        return '0 товаров'
    products_count.short_description = 'Товаров'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для товаров"""
    list_display = ('title', 'sku', 'section_link', 'price_special', 'price_retail', 'order', 'is_active', 'image_preview')
    list_filter = ('is_active', 'section__subcategory__category', 'section__subcategory', 'section', 'created_at')
    search_fields = ('title', 'sku', 'short_description', 'full_description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('order', 'is_active', 'price_special', 'price_retail')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    actions = ['make_active', 'make_inactive', 'duplicate_products', 'delete_selected_products']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'section', 'sku', 'is_active', 'order'),
            'description': 'Выберите раздел, в который будет добавлен товар.'
        }),
        ('Описание', {
            'fields': ('short_description', 'full_description'),
            'classes': ('collapse',)
        }),
        ('Цены и характеристики', {
            'fields': (
                'price', 'price_special', 'price_retail',
                'unit', 'wire_section', 'load_limit',
                'stock'
            )
        }),
        ('Изображение', {
            'fields': ('image', 'image_code', 'image_preview'),
            'description': 'Загрузите изображение через поле "Image" или укажите "Image code" для использования изображений с оригинального сайта. Формат image_code: код из пути /upload/resize_cache/iblock/{code}/...'
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def section_link(self, obj):
        """Ссылка на раздел"""
        if obj.section:
            url = reverse('admin:catalog_section_change', args=[obj.section.pk])
            return format_html('<a href="{}">{}</a>', url, str(obj.section))
        return '-'
    section_link.short_description = 'Раздел'

    def price_display(self, obj):
        """Отображение специальной цены"""
        if obj.price_special:
            return format_html('<strong>{:.0f} тг</strong>', obj.price_special)
        return format_html('{:.0f} тг', obj.price)
    price_display.short_description = 'Спец. цена'

    def image_preview(self, obj):
        """Превью изображения"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 150px; max-width: 150px; border: 1px solid #ddd; padding: 5px; border-radius: 4px;" />',
                obj.image.url
            )
        elif obj.image_code:
            # Если это путь к статическому файлу
            if obj.image_code.startswith('/static/'):
                image_url = obj.image_code
            # Если это полный URL
            elif obj.image_code.startswith('http'):
                image_url = obj.image_code
            else:
                # Пробуем загрузить с оригинального сайта
                image_url = f'https://group.ck-mitra.kz/upload/resize_cache/iblock/{obj.image_code}/310_310_2/{obj.image_code}.png'
            
            # Используем data URI для placeholder вместо несуществующего файла
            placeholder = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
            return format_html(
                '<img src="{}" style="max-height: 150px; max-width: 150px; border: 1px solid #ddd; padding: 5px; border-radius: 4px;" onerror="this.src=\'{}\'" />',
                image_url, placeholder
            )
        return format_html(
            '<div style="width: 150px; height: 150px; border: 1px dashed #ccc; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">Нет изображения</div>'
        )
    image_preview.short_description = 'Превью'

    def make_active(self, request, queryset):
        """Массовое действие: сделать товары активными"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано товаров: {updated}')
    make_active.short_description = 'Активировать выбранные товары'

    def make_inactive(self, request, queryset):
        """Массовое действие: сделать товары неактивными"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано товаров: {updated}')
    make_inactive.short_description = 'Деактивировать выбранные товары'

    def duplicate_products(self, request, queryset):
        """Массовое действие: дублировать товары"""
        count = 0
        for product in queryset:
            product.pk = None
            product.sku = f"{product.sku}_copy_{count}"
            product.title = f"{product.title} (копия)"
            product.save()
            count += 1
        self.message_user(request, f'Создано копий: {count}')
    duplicate_products.short_description = 'Дублировать выбранные товары'
    
    def delete_model(self, request, obj):
        """Удаление одного товара с проверкой связанных объектов"""
        try:
            # Проверяем наличие в заказах
            order_items_count = obj.order_items.count()
            if order_items_count > 0:
                self.message_user(
                    request,
                    f'Нельзя удалить товар "{obj.title}": он используется в {order_items_count} позициях заказов. '
                    f'Сначала удалите или измените заказы, содержащие этот товар.',
                    level='ERROR'
                )
                return
            
            obj.delete()
            self.message_user(request, f'Товар "{obj.title}" успешно удалён.')
        except Exception as e:
            self.message_user(request, f'Ошибка при удалении товара: {str(e)}', level='ERROR')
    
    def delete_selected_products(self, request, queryset):
        """Массовое удаление товаров с проверкой"""
        deleted = 0
        errors = []
        
        for product in queryset:
            try:
                # Проверяем наличие в заказах
                order_items_count = product.order_items.count()
                if order_items_count > 0:
                    errors.append(f'"{product.title}": используется в {order_items_count} позициях заказов')
                    continue
                
                product.delete()
                deleted += 1
            except Exception as e:
                errors.append(f'"{product.title}": {str(e)}')
        
        if deleted > 0:
            self.message_user(request, f'Удалено товаров: {deleted}')
        if errors:
            self.message_user(
                request,
                f'Не удалось удалить {len(errors)} товаров:\n' + '\n'.join(errors),
                level='ERROR'
            )
    delete_selected_products.short_description = 'Удалить выбранные товары'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('product', 'product_title', 'product_sku', 'quantity', 'price', 'total_price')
    autocomplete_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_phone', 'customer_email', 'status', 'total_amount_display', 'items_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'customer_email', 'id')
    readonly_fields = ('total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Детали заказа', {
            'fields': ('status', 'comment', 'total_amount')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_amount_display(self, obj):
        """Отображение общей суммы заказа"""
        amount = float(obj.total_amount) if obj.total_amount else 0.0
        formatted_amount = f'{amount:.2f}'
        return format_html('<strong>{} тг</strong>', formatted_amount)
    total_amount_display.short_description = 'Сумма заказа'

    def items_count(self, obj):
        """Количество позиций в заказе"""
        count = obj.items.count()
        return f'{count} позиций'
    items_count.short_description = 'Позиций'


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'lead_type', 'phone', 'email', 'processed', 'created_at')
    list_filter = ('lead_type', 'processed', 'created_at')
    search_fields = ('name', 'phone', 'email', 'message')
    list_editable = ('processed',)
    readonly_fields = ('created_at', 'updated_at', 'meta_display')
    
    fieldsets = (
        ('Тип заявки', {
            'fields': ('lead_type', 'processed')
        }),
        ('Контактная информация', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Сообщение', {
            'fields': ('message',)
        }),
        ('Дополнительная информация', {
            'fields': ('meta_display',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def meta_display(self, obj):
        """Отображение мета-данных"""
        if obj.meta:
            import json
            return format_html('<pre>{}</pre>', json.dumps(obj.meta, indent=2, ensure_ascii=False))
        return '-'
    meta_display.short_description = 'Мета-данные'
