from celery import shared_task
from django.conf import settings
from telegram import Bot
import jdatetime
from users.models import CustomUser
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, retry_backoff=True)  # Enable retries with backoff
def send_birthday_messages(self):
    """Sends birthday messages to users on their birthday."""

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    today = jdatetime.date.today()
    users = CustomUser.objects.filter(birth_date__isnull=False)

    for user in users:
        try:
            birth_date = jdatetime.date.fromgregorian(date=user.birth_date)
            if birth_date.month == today.month and birth_date.day == today.day:
                message = f"تولدت مبارک، {user.full_name}! 🎉 امیدواریم روز خاصی داشته باشی!"
                bot.send_message(chat_id=user.id, text=message)
                logger.info(f"Birthday message sent to {user.phone_number}")

        except Exception as exc:
            logger.error(f"Error sending birthday message to {user.phone_number}: {exc}", exc_info=True)
            # Retry the task, but with a maximum number of retries
            if self.request.retries < 3:  # Retry a maximum of 3 times
                raise self.retry(exc=exc, countdown=5)  # Retry after 5 seconds
            else:
                logger.error(f"Max retries reached for {user.phone_number}")