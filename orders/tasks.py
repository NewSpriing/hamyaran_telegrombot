from celery import shared_task
from telegram import Bot
from decouple import config
import jdatetime

@shared_task
def send_reminder(order_id, telegram_id, recipient_name, service_name, scheduled_time):
    bot_token = config('TELEGRAM_BOT_TOKEN')
    bot = Bot(token=bot_token)
    message = (
        f"یادآوری: شما یک خدمت پزشکی دارید!\n"
        f"دریافت‌کننده: {recipient_name}\n"
        f"خدمت: {service_name}\n"
        f"زمان: {scheduled_time}\n"
        f"لطفاً برای تأیid یا لغو اقدام کنید."
    )
    bot.send_message(chat_id=telegram_id, text=message)