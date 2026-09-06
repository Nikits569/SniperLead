from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(UserAdmin):
    list_display = ('email', 'name', 'plan', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'name', 'telegram', 'whatsapp')
    list_filter = ('plan', 'categories', 'is_staff', 'is_active', 'created_at', 'telegram_notification', 'email_notification')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name',)}),
        (_('Subscription & Settings'), {
            'fields': ('plan', 'start_at', 'end_at'),
        }),
        (_('Messengers & Notifications'), {
            'fields': (
                'telegram', 'telegram_notification',
                'whatsapp', 'whatsapp_notification',
                'email_notification'
            ),
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'email_verification_token')}),
    )

    readonly_fields = ('created_at', 'email_verification_token')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'plan', 'is_staff', 'is_superuser'),
        }),
    )