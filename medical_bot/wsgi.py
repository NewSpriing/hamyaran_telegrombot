"""
WSGI config for medical_bot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from medical_bot.views import initialize_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_bot.settings')

# Initialize Telegram application
initialize_application()

application = get_wsgi_application()