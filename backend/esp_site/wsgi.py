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

application = get_wsgi_application()
