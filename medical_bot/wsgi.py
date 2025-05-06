import os
from django.core.wsgi import get_wsgi_application
from medical_bot.views import initialize_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_bot.settings')

# Initialize Telegram application
initialize_application()

application = get_wsgi_application()