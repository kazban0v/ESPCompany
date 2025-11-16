from django.urls import path

from .views import (
    FrontendIndexView,
    LeadCreateView,
    CartSummaryView,
    CartItemView,
    CartItemRemoveView,
    CartClearView,
    OrderCreateView,
    ProductDetailView,
    SectionProductsView,
)

app_name = 'catalog'

urlpatterns = [
    path('', FrontendIndexView.as_view(), name='index'),
    path('api/leads/', LeadCreateView.as_view(), name='lead-create'),
    path('api/cart/', CartSummaryView.as_view(), name='cart-summary'),
    path('api/cart/items/', CartItemView.as_view(), name='cart-item'),
    path('api/cart/items/remove/', CartItemRemoveView.as_view(), name='cart-item-remove'),
    path('api/cart/clear/', CartClearView.as_view(), name='cart-clear'),
    path('api/orders/', OrderCreateView.as_view(), name='order-create'),
    path('api/product/detail/', ProductDetailView.as_view(), name='product-detail'),
    path('api/section/products/', SectionProductsView.as_view(), name='section-products'),
]

