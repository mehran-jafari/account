from django.db.models.signals import post_save  # ایمپورت سیگنال post_save جنگو
from codes.models import Code  # مدل Code
from users.models import CustomUser  # مدل CustomUser
from django.dispatch import receiver  # دکوراتور برای ثبت دریافت‌کننده سیگنال
from django.db import transaction  # برای مدیریت تراکنش‌های دیتابیس
import logging



logger = logging.getLogger(__name__)

@receiver(post_save, sender=CustomUser)
def post_save_generate_code(sender, instance, created, *args, **kwargs):
    """
    تابعی که پس از ذخیره مدل CustomUser اجرا می‌شود.
    - اگر کاربر جدید ایجاد شده باشد (created=True)، یک کد تأیید برایش می‌سازد.
    """
     # فقط برای کاربران جدید (نه هنگام آپدیت)
    if created:
        try:
            # غیرفعال کردن موقت سیگنال
            post_save.disconnect(post_save_generate_code, sender=CustomUser)
            
            with transaction.atomic():
                Code.objects.filter(user=instance).delete()
                Code.objects.create(user=instance)
        except Exception as e:
            logger.error(f"خطا در ایجاد کد برای کاربر {instance.id}: {e}")
            raise
        finally:
            # اتصال مجدد سیگنال در هر حالت
            post_save.connect(post_save_generate_code, sender=CustomUser)