import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_bot.settings')

app = Celery('medical_bot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()