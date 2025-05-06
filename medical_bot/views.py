import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from bot import setup_handlers
from decouple import config

logger = logging.getLogger(__name__)

# Initialize the Telegram bot application
application = Application.builder().token(config('TELEGRAM_BOT_TOKEN')).build()

# Setup bot handlers
setup_handlers(application)

@csrf_exempt
def webhook(request):
    """Handle incoming Telegram webhook requests."""
    try:
        if request.method == 'POST':
            # Parse JSON data from request.body
            update_data = json.loads(request.body.decode('utf-8'))
            update = Update.de_json(update_data, application.bot)
            if update:
                application.process_update(update)
                return HttpResponse(status=200)
            else:
                logger.error("Invalid update received")
                return HttpResponse(status=400)
        return HttpResponse(status=405)  # Method not allowed
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from request")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return HttpResponse(status=500)