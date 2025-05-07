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

    if request.method != "POST":
        logger.warning(f"Invalid HTTP method: {request.method}")
        return HttpResponse(status=405, content="Method Not Allowed")  # Correct status code

    try:
        # Deserialize the update
        update_data = request.body.decode('utf-8')  # Assuming JSON; adjust if needed
        # Ensure application is initialized before processing the update
        if application is None:
            await initialize_telegram_app()
        update = Update.de_json(update_data, application.bot)  # Use the module-level application
        logger.debug(f"Received update: {update.to_dict()}")  # Log the update details

        # Process the update
        await application.process_update(update)
        logger.info("Update processed successfully.")
        return HttpResponse(status=200, content="OK")  # Simple acknowledgment

    except ValueError as e:
        logger.error(f"Invalid JSON payload: {e}")
        return JsonResponse({"error": "Invalid request body"}, status=400)

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)  # Log with traceback
        return HttpResponse(status=500, content="Internal Server Error")

# Django signal to initialize on server start (or similar event)
@receiver(request_started)
def on_server_start(sender, **kwargs):
    """Initializes the Telegram bot when the server starts."""
    async def _async_init():
        await initialize_telegram_app()

    asyncio.run(_async_init())