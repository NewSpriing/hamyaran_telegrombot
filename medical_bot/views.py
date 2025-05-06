from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from decouple import config
from bot import setup_handlers

# Global Application instance (not initialized yet)
application = None

def initialize_application():
    """Initialize the Telegram application globally."""
    global application
    if application is None:
        application = Application.builder().token(config('TELEGRAM_BOT_TOKEN')).build()
        setup_handlers(application)
        return application
    return application

@csrf_exempt
async def webhook(request):
    """Handle Telegram webhook requests."""
    if request.method == 'POST':
        # Ensure application is initialized
        app = initialize_application()
        
        # Get the update from the request body
        update = Update.de_json(request.POST, app.bot)
        
        # Process the update asynchronously
        await app.process_update(update)
        
        return HttpResponse(status=200)
    return HttpResponse(status=400)