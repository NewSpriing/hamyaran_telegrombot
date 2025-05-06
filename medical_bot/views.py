import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from decouple import config
from bot import setup_handlers

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global Application instance (not initialized yet)
application = None

def initialize_application():
    """Initialize the Telegram application globally."""
    global application
    if application is None:
        logger.debug("Initializing Telegram Application")
        try:
            token = config('TELEGRAM_BOT_TOKEN')
            logger.debug(f"TELEGRAM_BOT_TOKEN: {token[:10]}...")  # Log first 10 chars for security
            application = Application.builder().token(token).build()
            setup_handlers(application)
            logger.debug("Application initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            raise
    else:
        logger.debug("Application already initialized")
    return application

@csrf_exempt
async def webhook(request):
    """Handle Telegram webhook requests."""
    logger.debug("Received webhook request")
    if request.method == 'POST':
        # Ensure application is initialized
        try:
            app = initialize_application()
            logger.debug("Application retrieved for webhook")
        except Exception as e:
            logger.error(f"Webhook initialization failed: {str(e)}")
            return HttpResponse(status=500)
        
        # Get the update from the request body
        try:
            update = Update.de_json(request.POST, app.bot)
            logger.debug("Update parsed successfully")
        except Exception as e:
            logger.error(f"Failed to parse update: {str(e)}")
            return HttpResponse(status=400)
        
        # Process the update asynchronously
        try:
            await app.process_update(update)
            logger.debug("Update processed successfully")
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Failed to process update: {str(e)}")
            return HttpResponse(status=500)
    logger.debug("Invalid request method")
    return HttpResponse(status=400)