import json

from decimal import Decimal, InvalidOperation

from django.http import JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from django.views import View
from django.views.generic import TemplateView
from django.template.loader import render_to_string

from django.db.models import Prefetch

from .models import Lead, Order, OrderItem, Category, Subcategory, Section, Subsection, Product


def _get_cart(session):
    cart = session.get('cart')
    if not isinstance(cart, dict):
        cart = {}
        session['cart'] = cart
    return cart


def _save_cart(session, cart):
    session['cart'] = cart
    session.modified = True


def _parse_price(value):
    if value is None:
        return Decimal('0.00')
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    cleaned = str(value).strip().replace(' ', '').replace('\xa0', '').replace(',', '.')
    if not cleaned:
        return Decimal('0.00')
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return Decimal('0.00')


def _cart_totals(cart):
    items = []
    total_quantity = 0
    total_amount = Decimal('0.00')

    for product_id, item in cart.items():
        try:
            qty = max(int(item.get('quantity', 0)), 0)
        except (TypeError, ValueError):
            qty = 0

        if qty <= 0:
            continue

        price = _parse_price(item.get('price'))
        subtotal = price * qty
        total_quantity += qty
        total_amount += subtotal

        try:
            product_id_int = int(product_id)
        except (TypeError, ValueError):
            product_id_int = product_id

        items.append({
            'product_id': product_id_int,
            'title': item.get('title', ''),
            'sku': item.get('sku', '') or '',
            'price': str(price.quantize(Decimal('0.01'))),
            'quantity': qty,
            'subtotal': str(subtotal.quantize(Decimal('0.01'))),
        })

    return {
        'items': items,
        'total_quantity': total_quantity,
        'total_amount': str(total_amount.quantize(Decimal('0.01'))),
    }


class FrontendIndexView(TemplateView):
    template_name = 'catalog/index.html'

    def get(self, request, *args, **kwargs):
        get_token(request)
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Создаем queryset для активных товаров
            active_products = Product.objects.filter(is_active=True).order_by('order', 'title')
            
            # Загружаем все активные категории с вложенными уровнями и товарами
            all_categories = Category.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'subcategories',
                    queryset=Subcategory.objects.filter(is_active=True).order_by('order', 'title').prefetch_related(
                        Prefetch(
                            'sections',
                            queryset=Section.objects.filter(is_active=True).order_by('order', 'title').prefetch_related(
                                Prefetch('products', queryset=active_products)
                            )
                        )
                    )
                )
            ).order_by('order', 'title')
            
            # Собираем все товары для отображения на странице
            all_products = list(active_products.select_related('section__subcategory__category'))
            
            context['categories'] = all_categories
            context['root_categories'] = all_categories  # Для совместимости со старыми шаблонами
            context['all_products'] = all_products
        except Exception as e:
            # Если ошибка с базой данных, возвращаем пустые списки
            context['categories'] = []
            context['root_categories'] = []
            context['all_products'] = []
            # Логируем ошибку для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading catalog data: {e}")
        
        return context


class LeadCreateView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        # Поддерживаем как JSON, так и form-data
        if request.content_type == 'application/json':
            try:
                payload = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return JsonResponse({'success': False, 'message': 'Неверный формат данных.'}, status=400)
        else:
            # Form-data
            payload = request.POST.dict()
        
        # Определяем тип заявки из поля 'type' или 'lead_type'
        lead_type = payload.get('type') or payload.get('lead_type', 'feedback')
        name = (payload.get('name') or '').strip()
        email = (payload.get('email') or '').strip()
        phone = (payload.get('phone') or '').strip()
        message = (payload.get('message') or '').strip()

        # Маппинг типов из формы в типы Lead
        type_mapping = {
            'callback': 'callback',
            'feedback': 'feedback',
            'consultation': 'consultation',
        }
        lead_type = type_mapping.get(lead_type, 'feedback')

        if lead_type not in dict(Lead.LeadType.choices):
            return JsonResponse({'success': False, 'message': 'Некорректный тип заявки.'}, status=400)

        if not name:
            return JsonResponse({'success': False, 'message': 'Укажите имя.'}, status=400)

        if not phone and not email:
            return JsonResponse({'success': False, 'message': 'Укажите телефон или email.'}, status=400)

        lead = Lead.objects.create(
            lead_type=lead_type,
            name=name,
            email=email,
            phone=phone,
            message=message,
            meta={
                'source': 'frontend',
                'raw_payload': payload,
            },
        )

        return JsonResponse(
            {'success': True, 'message': 'Заявка принята.', 'lead_id': lead.pk},
            status=201,
        )


class CartSummaryView(View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        cart = _get_cart(request.session)
        data = _cart_totals(cart)
        return JsonResponse({'success': True, **data})


class CartItemView(View):
    http_method_names = ['post', 'delete']

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'success': False, 'message': 'Неверный формат данных.'}, status=400)

        product_id = payload.get('product_id')
        quantity = payload.get('quantity', 1)

        title = (payload.get('title') or '').strip()
        sku = (payload.get('sku') or '').strip()
        price = _parse_price(payload.get('price'))

        if not product_id or not title:
            return JsonResponse({'success': False, 'message': 'Не указан товар.'}, status=400)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        cart = _get_cart(request.session)
        key = str(product_id)

        if quantity <= 0:
            cart.pop(key, None)
        else:
            existing = cart.get(key, {})
            current_qty = int(existing.get('quantity', 0))
            new_quantity = quantity
            if not payload.get('replace', False):
                new_quantity = current_qty + quantity

            cart[key] = {
                'title': title,
                'sku': sku,
                'price': str(price.quantize(Decimal('0.01'))),
                'quantity': max(1, min(new_quantity, 999)),
            }

        _save_cart(request.session, cart)
        data = _cart_totals(cart)
        return JsonResponse({'success': True, **data}, status=200)

    def delete(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'message': 'Метод не поддерживается.'}, status=405)


class CartItemRemoveView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'success': False, 'message': 'Неверный формат данных.'}, status=400)

        product_id = payload.get('product_id')
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Не указан товар.'}, status=400)

        cart = _get_cart(request.session)
        cart.pop(str(product_id), None)
        _save_cart(request.session, cart)
        data = _cart_totals(cart)
        return JsonResponse({'success': True, **data}, status=200)


class CartClearView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        request.session['cart'] = {}
        request.session.modified = True
        return JsonResponse({'success': True, 'items': [], 'total_quantity': 0, 'total_amount': '0.00'})


class OrderCreateView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'success': False, 'message': 'Неверный формат данных.'}, status=400)

        name = (payload.get('name') or '').strip()
        phone = (payload.get('phone') or '').strip()
        email = (payload.get('email') or '').strip()
        comment = (payload.get('comment') or '').strip()

        if not name:
            return JsonResponse({'success': False, 'message': 'Укажите имя.'}, status=400)
        if not phone and not email:
            return JsonResponse({'success': False, 'message': 'Укажите телефон или email.'}, status=400)

        cart = _get_cart(request.session)
        cart_data = _cart_totals(cart)
        if not cart_data['items']:
            return JsonResponse({'success': False, 'message': 'Корзина пуста.'}, status=400)

        order = Order.objects.create(
            customer_name=name,
            customer_phone=phone,
            customer_email=email,
            comment=comment,
        )

        for item in cart_data['items']:
            price = _parse_price(item.get('price'))
            title = item.get('title') or f'Товар {item.get("product_id")}'
            sku = item.get('sku', '') or ''
            OrderItem.objects.create(
                order=order,
                product=None,
                product_title=title,
                product_sku=sku,
                quantity=item['quantity'],
                price=price,
            )

        # корзина очищается после заказа
        request.session['cart'] = {}
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'message': 'Заказ принят. Мы свяжемся с вами для подтверждения.',
            'order_id': order.pk,
        }, status=201)


class ProductDetailView(View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        sku = request.GET.get('id') or request.GET.get('sku')
        if not sku:
            return HttpResponse('Товар не найден', status=404)
        
        try:
            product = Product.objects.get(sku=sku, is_active=True)
        except Product.DoesNotExist:
            return HttpResponse('Товар не найден', status=404)
        
        html = render_to_string('catalog/product_detail.html', {
            'product': product,
        }, request=request)
        
        return HttpResponse(html)


class SectionProductsView(View):
    """AJAX endpoint для загрузки товаров раздела с пагинацией"""
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        section_id = request.GET.get('section_id')
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 9))
        
        if not section_id:
            return JsonResponse({'success': False, 'message': 'Не указан раздел'}, status=400)
        
        try:
            section = Section.objects.get(id=section_id, is_active=True)
        except Section.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Раздел не найден'}, status=404)
        
        # Получаем товары с пагинацией
        products = section.products.filter(is_active=True).order_by('order', 'title')[offset:offset + limit]
        total_count = section.products.filter(is_active=True).count()
        
        # Рендерим HTML для товаров
        products_html = render_to_string('catalog/_product_list.html', {
            'products': products,
        }, request=request)
        
        has_more = (offset + limit) < total_count
        
        return JsonResponse({
            'success': True,
            'html': products_html,
            'has_more': has_more,
            'total_count': total_count,
            'loaded_count': offset + len(products),
        })
