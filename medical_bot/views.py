from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from decouple import config
import json

# Global Telegram Application instance
bot_application = Application.builder().token(config('TELEGRAM_BOT_TOKEN')).build()

@csrf_exempt
async def webhook(request):
    if request.method == 'POST':
        update = Update.de_json(json.loads(request.body.decode('utf-8')), bot=bot_application.bot)
        await bot_application.process_update(update)
        return HttpResponse(status=200)
    return HttpResponse(status=400)