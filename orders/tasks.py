from celery import shared_task
from django.conf import settings  # Import settings for TELEGRAM_BOT_TOKEN
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from django.utils import timezone  # Use Django's timezone for consistency
import jdatetime
import logging
from .models import Order

logger = logging.getLogger(__name__)


@shared_task
def test_task():
    """A test task to ensure Celery is working."""
    logger.info("Test task executed successfully")
    return "Test task completed"


@shared_task
def send_reminder():
    """
    Sends reminders to users about their upcoming orders.
    """
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)  # Access token from settings
    now = timezone.now()  # Use Django's timezone-aware now()
    orders = Order.objects.filter(
        status='confirmed',
        scheduled_time__gte=now,
        scheduled_time__lte=now + timezone.timedelta(hours=24)  # Use Django's timedelta
    )
    logger.info(f"Found {orders.count()} orders for reminders.")

    for order in orders:
        try:
            scheduled_time_gregorian = order.scheduled_time
            scheduled_time_jalali = jdatetime.datetime.fromgregorian(dt=scheduled_time_gregorian)
            time_diff = scheduled_time_gregorian - now
            user = order.user
            recipient_name = order.recipient.full_name if order.recipient else user.full_name
            keyboard = [
                [InlineKeyboardButton("تأیید", callback_data=f'confirm_{order.id}'),
                 InlineKeyboardButton("لغو", callback_data=f'cancel_{order.id}')],
                [InlineKeyboardButton("تماس با پشتیبانی", callback_data='contact_support')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            hours_until_event = time_diff.total_seconds() / 3600

            if 23.5 <= hours_until_event <= 24.5:  # 24-hour reminder
                message = (
                    f"یادآوری: خدمت {order.service.name} برای {recipient_name} "
                    f"در تاریخ {scheduled_time_jalali.strftime('%Y/%m/%d %H:%M:%S')} در آدرس {order.address.title} "
                    f"برنامه‌ریزی شده است."
                )
                bot.send_message(chat_id=user.id, text=message, reply_markup=reply_markup)
                logger.info(f"24-hour reminder sent for order {order.id} to user {user.id}")

            elif 0.5 <= hours_until_event <= 1.5:  # 1-hour reminder
                message = (
                    f"یادآوری: خدمت {order.service.name} برای {recipient_name} "
                    f"کمتر از یک ساعت دیگر در تاریخ {scheduled_time_jalali.strftime('%Y/%m/%d %H:%M:%S')} در آدرس {order.address.title} "
                    f"برگزار خواهد شد."
                )
                bot.send_message(chat_id=user.id, text=message, reply_markup=reply_markup)
                logger.info(f"1-hour reminder sent for order {order.id} to user {user.id}")

        except Exception as e:
            logger.error(f"Failed to send reminder for order {order.id}: {e}", exc_info=True)