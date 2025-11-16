from decimal import Decimal

from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        abstract = True


class Category(TimestampedModel):
    """Категория - первый уровень"""
    title = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-адрес', unique=True, max_length=255)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    order = models.PositiveIntegerField('Порядок отображения', default=0, help_text='Порядок отображения')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'title']

    def __str__(self) -> str:
        return self.title


class Subcategory(TimestampedModel):
    """Подкатегория - второй уровень"""
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name='Категория',
    )
    title = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-адрес', max_length=255)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    order = models.PositiveIntegerField('Порядок отображения', default=0, help_text='Порядок отображения')

    class Meta:
        verbose_name = 'Подкатегория'
        verbose_name_plural = 'Подкатегории'
        ordering = ['order', 'title']
        unique_together = [['category', 'slug']]

    def __str__(self) -> str:
        return f'{self.category.title} → {self.title}'


class Section(TimestampedModel):
    """Раздел - третий уровень"""
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='Подкатегория',
    )
    title = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-адрес', max_length=255)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    order = models.PositiveIntegerField('Порядок отображения', default=0, help_text='Порядок отображения')

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'
        ordering = ['order', 'title']
        unique_together = [['subcategory', 'slug']]

    def __str__(self) -> str:
        return f'{self.subcategory.category.title} → {self.subcategory.title} → {self.title}'
    
    def get_products_count(self):
        """Возвращает количество активных товаров в разделе"""
        return self.products.filter(is_active=True).count()


class Subsection(TimestampedModel):
    """Товарная группа - четвертый уровень"""
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='subsections',
        verbose_name='Раздел',
    )
    title = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-адрес', max_length=255)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    order = models.PositiveIntegerField('Порядок отображения', default=0, help_text='Порядок отображения')

    class Meta:
        verbose_name = 'Товарная группа'
        verbose_name_plural = 'Товарные группы'
        ordering = ['order', 'title']
        unique_together = [['section', 'slug']]

    def __str__(self) -> str:
        return f'{self.section.subcategory.category.title} → {self.section.subcategory.title} → {self.section.title} → {self.title}'


class Product(TimestampedModel):
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        related_name='products',
        null=True,
        blank=True,
        verbose_name='Раздел',
    )
    title = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-адрес', unique=True, max_length=255)
    sku = models.CharField('Маркировка (SKU)', max_length=128, help_text='Маркировка', unique=True)
    short_description = models.TextField('Краткое описание', blank=True)
    full_description = models.TextField('Полное описание', blank=True)
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2, default=0)
    stock = models.PositiveIntegerField('Остаток на складе', default=0)
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField('Активен', default=True)
    unit = models.CharField('Единица измерения', max_length=32, blank=True)
    price_special = models.DecimalField('Специальная цена', max_digits=12, decimal_places=2, null=True, blank=True)
    price_retail = models.DecimalField('Розничная цена', max_digits=12, decimal_places=2, null=True, blank=True)
    wire_section = models.CharField('Сечение провода', max_length=64, blank=True)
    load_limit = models.CharField('Предельная нагрузка', max_length=64, blank=True)
    image_code = models.CharField('Код изображения', max_length=128, blank=True, help_text='Код для загрузки изображения с оригинального сайта')
    order = models.PositiveIntegerField('Порядок отображения', default=0)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['order', 'title']

    def __str__(self) -> str:
        return self.title

    @property
    def display_price(self):
        return self.price_special or self.price

    @property
    def display_price_retail(self):
        return self.price_retail or self.price

    @property
    def image_url(self):
        if self.image:
            # Используем url напрямую - Django уже добавляет MEDIA_URL
            return self.image.url
        if self.image_code:
            # Игнорируем product-placeholder.png
            if 'product-placeholder.png' in self.image_code:
                # Пропускаем и переходим к следующей проверке
                pass
            # Проверяем, что image_code не является полным URL
            elif self.image_code.startswith('http'):
                # Если это полный URL, используем его напрямую
                return self.image_code
            # Если это путь к статическому файлу (начинается с /static/)
            elif self.image_code.startswith('/static/'):
                # Проверяем, что это не product-placeholder.png
                if 'product-placeholder.png' not in self.image_code:
                    return self.image_code
            # Если это просто код
            else:
                return f'/upload/resize_cache/iblock/{self.image_code}/310_310_2/{self.image_code}.png'
        
        # Пробуем найти изображение в папке elektrotehnicheskij-zavod-kvt по названию товара (title)
        # ИСПРАВЛЕНИЕ: Ищем по title, а не по SKU, потому что SKU - это числовой код,
        # а имена файлов соответствуют обозначениям товаров (названиям)
        if self.title:
            import os
            from pathlib import Path
            from django.conf import settings
            
            # Нормализуем название товара для поиска файла
            import re
            
            # Убираем лишние символы и пробелы, переводим в верхний регистр
            title_clean = re.sub(r'[^\w\-/]', '', str(self.title).upper().strip())
            normalized_title = re.sub(r'\s+', '', title_clean)
            
            # Путь к папке с изображениями
            images_dir = Path(settings.BASE_DIR) / 'static' / 'img' / 'elektrotehnicheskij-zavod-kvt'
            
            if images_dir.exists():
                # Ищем файл по точному совпадению
                for ext in ['.jpg', '.jpeg', '.png']:
                    # Пробуем разные варианты имени файла
                    variants = [
                        normalized_title + ext,
                        normalized_title.replace('/', '_') + ext,
                        normalized_title.replace('-', '_') + ext,
                        title_clean + ext,
                        title_clean.replace('/', '_') + ext,
                        title_clean.replace('-', '_') + ext,
                    ]
                    
                    for variant in variants:
                        img_path = images_dir / variant
                        if img_path.exists():
                            return f'/static/img/elektrotehnicheskij-zavod-kvt/{variant}'
                
                # Пробуем найти по частичному совпадению (более гибкий поиск)
                title_variants = [
                    normalized_title,
                    normalized_title.replace('/', '_').replace('-', '_'),
                    title_clean,
                    title_clean.replace('/', '_').replace('-', '_'),
                ]
                
                for img_file in list(images_dir.glob('*.jpg')) + list(images_dir.glob('*.png')) + list(images_dir.glob('*.jpeg')):
                    img_name_no_ext = os.path.splitext(img_file.name)[0]
                    img_name_normalized = re.sub(r'[^\w\-/]', '', img_name_no_ext.upper()).replace(' ', '').replace('/', '_').replace('-', '_')
                    
                    # Проверяем все варианты названия товара
                    for title_variant in title_variants:
                        title_variant_clean = title_variant.replace('/', '_').replace('-', '_')
                        
                        # Точное совпадение
                        if title_variant_clean == img_name_normalized:
                            return f'/static/img/elektrotehnicheskij-zavod-kvt/{img_file.name}'
                        
                        # Частичное совпадение (минимум 70% совпадения)
                        if len(title_variant_clean) >= 3 and len(img_name_normalized) >= 3:
                            if title_variant_clean in img_name_normalized:
                                match_ratio = len(title_variant_clean) / len(img_name_normalized)
                                if match_ratio >= 0.7:
                                    return f'/static/img/elektrotehnicheskij-zavod-kvt/{img_file.name}'
                            elif img_name_normalized in title_variant_clean:
                                match_ratio = len(img_name_normalized) / len(title_variant_clean)
                                if match_ratio >= 0.7:
                                    return f'/static/img/elektrotehnicheskij-zavod-kvt/{img_file.name}'
        
        # Возвращаем data URI для placeholder (1x1 прозрачный PNG)
        # Это предотвратит 404 ошибки и не будет пытаться загрузить несуществующий файл
        return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

    def save(self, *args, **kwargs):
        if self.price_special is not None:
            self.price = self.price_special
        super().save(*args, **kwargs)


class Order(TimestampedModel):
    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        IN_PROGRESS = 'in_progress', 'В обработке'
        DONE = 'done', 'Завершён'
        CANCELLED = 'cancelled', 'Отменён'

    customer_name = models.CharField('Имя клиента', max_length=255)
    customer_email = models.EmailField('Email клиента', blank=True)
    customer_phone = models.CharField('Телефон клиента', max_length=32)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.NEW)
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Заказ #{self.pk} ({self.get_status_display()})'

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True, related_name='order_items', verbose_name='Товар')
    product_title = models.CharField('Название товара', max_length=255)
    product_sku = models.CharField('Маркировка товара', max_length=128, blank=True)
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self) -> str:
        title = self.product.title if self.product else self.product_title
        return f'{title} x {self.quantity}'

    @property
    def total_price(self):
        price = self.price if self.price is not None else Decimal('0')
        quantity = self.quantity if self.quantity is not None else 0
        return price * quantity


class Lead(TimestampedModel):
    class LeadType(models.TextChoices):
        CALLBACK = 'callback', 'Обратный звонок'
        CONSULTATION = 'consultation', 'Консультация'
        PRICE_REQUEST = 'price_request', 'Запрос прайса'
        FEEDBACK = 'feedback', 'Связаться с нами'

    lead_type = models.CharField(
        'Тип заявки',
        max_length=32,
        choices=LeadType.choices,
        default=LeadType.FEEDBACK,
    )
    name = models.CharField('Имя', max_length=255)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Телефон', max_length=32, blank=True)
    message = models.TextField('Сообщение', blank=True)
    meta = models.JSONField('Мета-данные', blank=True, null=True)
    processed = models.BooleanField('Обработано', default=False)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['processed', '-created_at']

    def __str__(self) -> str:
        return f'{self.get_lead_type_display()} от {self.name}'
