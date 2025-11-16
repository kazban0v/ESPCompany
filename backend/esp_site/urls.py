"""
URL configuration for esp_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalog.urls', namespace='catalog')),
]

# В DEBUG режиме добавляем статические файлы через Django
# В production WhiteNoise обслуживает их автоматически
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Добавляем маршруты для bitrix и upload только если директории существуют
    from pathlib import Path
    bitrix_path = settings.BASE_DIR.parent / 'bitrix'
    upload_path = settings.BASE_DIR.parent / 'upload'
    if bitrix_path.exists():
        urlpatterns += static('bitrix/', document_root=bitrix_path)
    if upload_path.exists():
        urlpatterns += static('upload/', document_root=upload_path)
    # Добавляем маршрут для favicon.ico
    from django.views.generic import RedirectView
    urlpatterns += [
        path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'img/favicon.ico', permanent=True)),
    ]
