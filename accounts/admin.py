from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'company', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'company', 'is_active', 'email_verified', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Company Information', {'fields': ('company', 'role')}),
        ('Profile', {'fields': ('avatar', 'phone', 'timezone', 'email_verified')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Company Information', {'fields': ('company', 'role')}),
        ('Profile', {'fields': ('phone', 'timezone')}),
    )
