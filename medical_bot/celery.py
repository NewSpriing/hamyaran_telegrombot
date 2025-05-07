import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_bot.settings')

app = Celery('medical_bot')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-birthday-messages-every-day': {
        'task': 'medical_bot.tasks.send_birthday_messages',
        'schedule': crontab(hour=8, minute=0),  # Run daily at 8:00 AM
    },
}

app.conf.timezone = 'Asia/Tehran'  # Ensure Celery uses the correct timezone