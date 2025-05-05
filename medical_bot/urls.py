from django.contrib import admin
from django.urls import path, include
from .views import webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/services/', include('services.urls')),
    path('api/orders/', include('orders.urls')),
    path('telegram/webhook/', webhook, name='webhook'),
]