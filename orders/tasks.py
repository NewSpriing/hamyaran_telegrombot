from celery import shared_task
from django_jalali.db import models as jmodels
from orders.models import Order
from users.models import CustomUser
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from decouple import config
import jdatetime
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def test_task():
    logger.info("Test task executed successfully")
    return "Test task completed"

@shared_task
def send_reminder():
    bot = Bot(token=config('TELEGRAM_BOT_TOKEN'))
    now = jdatetime.datetime.now()
    orders = Order.objects.filter(
        status='confirmed',
        scheduled_time__gte=now,
        scheduled_time__lte=now + jdatetime.timedelta(hours=24)
    )
    for order in orders:
        time_diff = order.scheduled_time - now
        user = order.user
        recipient_name = order.recipient.full_name if order.recipient else user.full_name
        keyboard = [
            [InlineKeyboardButton("تأیید", callback_data=f'confirm_{order.id}'),
             InlineKeyboardButton("لغو", callback_data=f'cancel_{order.id}')],
            [InlineKeyboardButton("تماس با پشتیبانی", callback_data='contact_support')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if 23.5 <= time_diff.total_seconds() / 3600 <= 24.5:  # 24-hour reminder
            message = (
                f"یادآوری: خدمت {order.service.name} برای {recipient_name} "
                f"در تاریخ {order.scheduled_time} در آدرس {order.address.title} "
                f"برنامه‌ریزی شده است."
            )
            bot.send_message(chat_id=user.telegram_id, text=message, reply_markup=reply_markup)
        elif 0.5 <= time_diff.total_seconds() / 3600 <= 1.5:  # 1-hour reminder
            message = (
                f"یادآوری: خدمت {order.service.name} برای {recipient_name} "
                f"کمتر از یک ساعت دیگر در {order.scheduled_time} در آدرس {order.address.title} "
                f"انجام خواهد شد."
            )
            bot.send_message(chat_id=user.telegram_id, text=message, reply_markup=reply_markup)
            