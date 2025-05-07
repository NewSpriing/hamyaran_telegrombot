from django.contrib import admin
from .models import Order

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service', 'address', 'scheduled_time', 'status']
    list_filter = ['status', 'scheduled_time']
    search_fields = ['user__phone_number', 'service__name', 'address__title']
    readonly_fields = ['created_at']  # Make created_at read-only in admin

admin.site.register(Order, OrderAdmin)