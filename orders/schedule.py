from celery import Celery
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

def setup_periodic_tasks():
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.MINUTES,
    )
    PeriodicTask.objects.get_or_create(
        interval=schedule,
        name='Send order reminders',
        task='orders.tasks.send_reminder',
        defaults={'args': json.dumps([])},
    )