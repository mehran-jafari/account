from django.contrib import admin
from django.utils.html import format_html
from .models import Code
from django.utils import timezone

@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):
    """پنل مدیریت برای مدل Code"""
    
    # فیلدهایی که در لیست نمایش داده می‌شوند
    list_display = ('number', 'user', 'created_at', 'expires_at', 'is_used', 'is_valid_display', 'time_remaining')
    
    # فیلدهای قابل جستجو
    search_fields = ('number', 'user__username', 'user__phone_number')
    
    # فیلترهای سمت راست
    list_filter = ('is_used', 'created_at', 'expires_at')
    
    # فیلدهای قابل ویرایش در لیست
    list_editable = ('is_used',)
    
    # فیلدهای فقط خواندنی
    readonly_fields = ('number', 'user', 'created_at', 'expires_at', 'is_valid_display', 'time_remaining')
    
    # ترتیب فیلدها در صفحه ویرایش
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('number', 'user')
        }),
        ('وضعیت', {
            'fields': ('is_used', 'is_valid_display', 'time_remaining')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'expires_at')
        }),
    )
    
    # تعداد آیتم‌ها در هر صفحه
    list_per_page = 20
    
    # نمایش وضعیت اعتبار به صورت رنگی
    def is_valid_display(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">معتبر</span>')
        return format_html('<span style="color: red;">منقضی</span>')
    is_valid_display.short_description = 'وضعیت اعتبار'
    
    # نمایش زمان باقی‌مانده تا انقضا
    def time_remaining(self, obj):
        if obj.expires_at > timezone.now():
            remaining = obj.expires_at - timezone.now()
            minutes = int(remaining.total_seconds() / 60)
            seconds = int(remaining.total_seconds() % 60)
            return f"{minutes} دقیقه و {seconds} ثانیه"
        return "منقضی شده"
    time_remaining.short_description = 'زمان باقی‌مانده'
    
    # غیرفعال کردن امکان اضافه کردن دستی (کدها باید خودکار تولید شوند)
    def has_add_permission(self, request):
        return False
    
    # نمایش کاربر به صورت لینک
    def user(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse("admin:users_customuser_change", args=(obj.user.id,))
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user.short_description = 'کاربر'
    
    # سفارشی‌سازی نمایش تاریخ‌ها
    def created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at.short_description = 'تاریخ ایجاد'
    
    def expires_at(self, obj):
        return obj.expires_at.strftime("%Y-%m-%d %H:%M:%S")
    expires_at.short_description = 'تاریخ انقضا'