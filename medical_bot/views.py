import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application, CallbackContext
from decouple import config
from bot import setup_handlers
from django.dispatch import receiver
from django.urls import path
from django.core.signals import request_started
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Module-level Application instance
application: Application = None  # Initialize as None with type hint

async def initialize_telegram_app() -> Application:
    """Initializes the Telegram Application instance."""
    global application
    if application is None:
        token = config('TELEGRAM_BOT_TOKEN')
        logger.info(f"Initializing Telegram bot with token: {token[:10]}...")  # Log first 10 characters
        try:
            application = Application.builder().token(token).read_timeout(30).write_timeout(30).connect_timeout(30).build()
            setup_handlers(application)
            await application.initialize()  # Initialize the application
            logger.info("Telegram bot initialized.")
        except Exception as e:
            logger.error(f"Error during Telegram bot initialization: {e}", exc_info=True)
            raise
    return application

@csrf_exempt
async def telegram_webhook(request):
    """Handles incoming Telegram updates via webhook."""
    # ... (بقیه کد webhook شما)