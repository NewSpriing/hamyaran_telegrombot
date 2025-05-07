from django.contrib import admin
from .models import ServiceCategory, Service

class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']
    list_filter = ['parent']
    search_fields = ['name']
    prepopulated_fields = {'name': ('name',)}  # Auto-generate slug from name

admin.site.register(ServiceCategory, ServiceCategoryAdmin)

class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration']
    list_filter = ['category']
    search_fields = ['name', 'description']

admin.site.register(Service, ServiceAdmin)