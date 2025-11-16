#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Passenger WSGI file for Timeweb Django deployment
"""
import sys
import os

# Добавляем путь к проекту в sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Настраиваем переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esp_site.settings')

# Импортируем WSGI приложение Django
from esp_site.wsgi import application

# Passenger ожидает переменную application
# (уже определена выше через import)

