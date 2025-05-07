import os
import logging
from django.core.wsgi import get_wsgi_application
from medical_bot.views import initialize_telegram_app  # تغییر نام تابع
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_bot.settings')

# Initialize Telegram application
try:
    logger.debug("Starting Telegram application initialization in WSGI")
    asyncio.run(initialize_telegram_app())  # اجرای تابع آسنکرون با asyncio.run
    logger.debug("Telegram application initialized in WSGI")
except Exception as e:
    logger.error(f"Failed to initialize Telegram application in WSGI: {str(e)}")
    raise

application = get_wsgi_application()