from django.contrib import admin
from .models import CustomUser, Address, FamilyMember

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'telegram_id', 'region')
    search_fields = ('full_name', 'phone_number', 'telegram_id')
    list_filter = ('gender', 'region')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'full_address')
    search_fields = ('title', 'full_address', 'user__full_name')
    list_filter = ('user',)

@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'relationship', 'age', 'gender')
    search_fields = ('full_name', 'user__full_name', 'relationship')
    list_filter = ('relationship', 'gender', 'user')