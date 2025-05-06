from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from decouple import config
from bot import setup_handlers

@csrf_exempt
async def webhook(request):
    """Handle Telegram webhook requests."""
    if request.method == 'POST':
        # Initialize the Telegram application
        application = Application.builder().token(config('TELEGRAM_BOT_TOKEN')).build()
        setup_handlers(application)
        
        # Get the update from the request body
        update = Update.de_json(request.POST, application.bot)
        
        # Process the update asynchronously
        await application.process_update(update)
        
        return HttpResponse(status=200)
    return HttpResponse(status=400)