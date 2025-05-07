
# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address, FamilyMember, Document

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['phone_number', 'full_name', 'gender', 'email']  # Removed 'age' from list_display
    list_filter = ['gender']
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'birth_date', 'gender', 'medical_conditions', 'email', 'region')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'full_name', 'gender', 'password')  # Removed password1/2
        }),
    )
    search_fields = ['phone_number', 'full_name']
    ordering = ['phone_number']

class AddressAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'full_address']
    search_fields = ['title', 'full_address']
    list_filter = ['user']

class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'relationship', 'gender']
    search_fields = ['full_name']
    list_filter = ['relationship', 'gender']

class DocumentAdmin(admin.ModelAdmin):
    list_display = ['description', 'family_member', 'uploaded_at']
    search_fields = ['description']
    list_filter = ['uploaded_at']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(FamilyMember, FamilyMemberAdmin)
admin.site.register(Document, DocumentAdmin)
