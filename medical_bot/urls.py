from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
import logging
from .views import telegram_webhook  # Renamed for clarity

logger = logging.getLogger(__name__)

def test_webhook(request):
    """Simple view to test webhook accessibility."""
    logger.debug("Test webhook endpoint accessed")
    return HttpResponse("Webhook endpoint is accessible")

def webhook_logs(request):
    """View to display webhook logs (for debugging)."""
    try:
        with open('webhook_logs.log', 'r') as f:
            logs = f.readlines()
        return HttpResponse("<br>".join(logs), content_type="text/html")
    except FileNotFoundError:
        logger.warning("Webhook log file not found.")
        return JsonResponse({"error": "Log file not found"}, status=404)
    except Exception as e:
        logger.error(f"Error reading webhook logs: {e}", exc_info=True)
        return JsonResponse({"error": f"Error reading logs: {e}"}, status=500)

def home(request):
    """Simple API root view."""
    logger.debug("Root endpoint accessed")
    return JsonResponse({"message": "Medical Bot API is running"}, status=200)

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/services/', include('services.urls')),
    path('api/orders/', include('orders.urls')),
    path('telegram/webhook/', telegram_webhook, name='telegram_webhook'),  # Consistent naming
    path('telegram/test/', test_webhook, name='test_webhook'),
    path('telegram/logs/', webhook_logs, name='webhook_logs'),
]