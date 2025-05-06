from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from decouple import config
import json

# Initialize the Telegram bot application
TOKEN = config('TELEGRAM_BOT_TOKEN')
application = Application.builder().token(TOKEN).build()

# Import bot handlers (we'll set this up after updating bot.py)
from bot import setup_handlers

# Setup handlers
setup_handlers(application)

@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), None)
        application = Application.builder().token(config('TELEGRAM_BOT_TOKEN')).build()
        setup_handlers(application)
        application.process_update(update)
        return HttpResponse(status=200)
    return HttpResponse(status=400)