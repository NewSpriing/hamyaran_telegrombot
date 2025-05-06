from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from bot import webhook_update
import logging

logger = logging.getLogger(__name__)

def test_webhook(request):
    logger.debug("Test webhook endpoint accessed")
    return HttpResponse("Webhook endpoint is accessible")

def webhook_logs(request):
    try:
        logs = []
        with open('webhook_logs.log', 'r') as f:
            logs = f.readlines()
        return HttpResponse("<br>".join(logs), content_type="text/html")
    except Exception as e:
        logger.error("Error reading webhook logs: %s", e)
        return HttpResponse(f"Error: {e}", status=500)

def home(request):
    logger.debug("Root endpoint accessed")
    return HttpResponse("Medical Bot API is running", status=200)

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/services/', include('services.urls')),
    path('api/orders/', include('orders.urls')),
    path('telegram/webhook/', csrf_exempt(webhook_update), name='webhook'),
    path('telegram/test/', test_webhook, name='test_webhook'),
    path('telegram/logs/', webhook_logs, name='webhook_logs'),
]
