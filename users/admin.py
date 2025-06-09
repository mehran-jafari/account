from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import CustomUser
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    list_display = ('username_link', 'display_phone_number', 'email', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'phone_number', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 20
    readonly_fields = (
        'last_login', 'date_joined',
        'last_login_ip', 'last_login_at',
        'failed_login_attempts', 'account_locked_until'
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('اطلاعات شخصی'), {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        (_('دسترسی‌ها'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('امنیت حساب'), {
            'fields': ('last_login_ip', 'last_login_at', 'failed_login_attempts', 'account_locked_until'),
        }),
        (_('تاریخ‌های مهم'), {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone_number', 'email', 'password1', 'password2'),
        }),
    )

    def display_phone_number(self, obj):
        if obj.phone_number:
            return format_html('<span dir="ltr">{}</span>', obj.phone_number)
        return "-"
    display_phone_number.short_description = _('شماره تلفن')

    def username_link(self, obj):
        url = reverse("admin:users_customuser_change", args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj.username)
    username_link.short_description = _('نام کاربری')

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

# ثبت مدل CustomUser با پنل مدیریت سفارشی
admin.site.register(CustomUser, CustomUserAdmin)