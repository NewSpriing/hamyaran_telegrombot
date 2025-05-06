import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_bot.settings')

app = Celery('medical_bot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_bot.settings')

app.conf.beat_schedule = {
    'send-birthday-messages-every-day': {
        'task': 'medical_bot.tasks.send_birthday_messages',
        'schedule': crontab(hour=8, minute=0),  # Run daily at 8:00 AM
    },
}