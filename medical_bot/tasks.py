from celery import shared_task
from django.conf import settings
from telegram import Bot
import jdatetime
from users.models import CustomUser

@shared_task
def send_birthday_messages():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    today = jdatetime.date.today()
    users = CustomUser.objects.filter(birth_date__isnull=False)
    for user in users:
        birth_date = jdatetime.date.fromgregorian(date=user.birth_date)
        if birth_date.month == today.month and birth_date.day == today.day:
            message = f"تولدت مبارک، {user.full_name}! 🎉 امیدواریم روز خاصی داشته باشی!"
            try:
                bot.send_message(chat_id=user.id, text=message)
            except Exception as e:
                print(f"Error sending birthday message to {user.phone_number}: {e}")