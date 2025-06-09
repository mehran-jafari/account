
import secrets
import time
import logging
from datetime import timedelta
from django.db import models, transaction
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser




logger = logging.getLogger(__name__)


class CodeManager(models.Manager):
    """مدیریت سفارشی برای مدل Code"""
    
    def create_verification_code(self, user):
        """ایجاد کد تأیید با مدیریت خطا"""
        try:
            return Code.objects.create(user=user)
        except Exception as e:
            logger.error(f"Failed to create verification code for user {user.id}: {e}")
            raise

class Code(models.Model):
    """
    مدل پیشرفته برای مدیریت کدهای تأیید کاربران
    ویژگی‌ها:
    - تولید کد 5 رقمی امن
    - اعتبارسنجی خودکار
    - مدیریت زمان انقضا
    - جلوگیری از کدهای تکراری
    """
    
    number = models.CharField(
        max_length=5,
        validators=[
            MinLengthValidator(5),
            RegexValidator(
                regex=r'^\d+$',
                message="کد باید فقط شامل اعداد باشد."
            )
        ],
        verbose_name="کد تأیید",
        help_text="کد 5 رقمی ارسال شده به کاربر"
    )
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='verification_codes',
        verbose_name="کاربر"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    
    expires_at = models.DateTimeField(
        verbose_name="تاریخ انقضا"
    )
    
    is_used = models.BooleanField(
        default=False,
        verbose_name="استفاده شده"
    )

    objects = CodeManager()

    class Meta:
        verbose_name = "کد تأیید"
        verbose_name_plural = "کدهای تأیید"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['number', 'is_used']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        """نمایش خوانا از کد و کاربر مربوطه با وضعیت اعتبار"""
        return f"کد {self.number} برای {self.user.username} ({'معتبر' if self.is_valid() else 'منقضی'})"
    
    
    def save(self, *args, **kwargs):
        """
        منطق سفارشی ذخیره:
        - تولید کد منحصر به فرد برای رکوردهای جدید
        - تنظیم زمان انقضا
        - مدیریت شرایط رقابتی
        """
        if not self.pk:
            self._generate_unique_code()
        super().save(*args, **kwargs)
    
    def _generate_unique_code(self):
        """تولید کد منحصر به فرد با مکانیزم بازگشتی"""
        max_attempts = 20
        for attempt in range(1, max_attempts + 1):
            try:
                with transaction.atomic():
                    code = ''.join(secrets.choice('0123456789') for _ in range(5))
                    if not Code.objects.filter(number=code, is_used=False).exists():
                        self.number = code
                        self.expires_at = timezone.now() + timedelta(minutes=5)
                        return
            
            except Exception as e:
                logger.warning(f"Attempt {attempt}: Failed to generate code - {str(e)}")
            
            if attempt < max_attempts:
                time.sleep(0.1 * attempt)
        
        raise ValueError("امکان تولید کد منحصر به فرد وجود ندارد پس از 20 تلاش")

    def is_valid(self):
        """بررسی اعتبار کد"""
        return not self.is_used and self.expires_at > timezone.now()
    
    def mark_as_used(self):
        """علامت گذاری کد به عنوان استفاده شده"""
        self.is_used = True
        self.save(update_fields=['is_used'])

@receiver(post_save, sender=CustomUser)
def handle_user_creation(sender, instance, created, **kwargs):
    """
    سیگنال برای ایجاد خودکار کد تأیید هنگام ثبت نام کاربر جدید
    ویژگی‌ها:
    - غیرفعال کردن موقت سیگنال برای جلوگیری از حلقه بی‌نهایت
    - مدیریت تراکنش
    - لاگ خطاها
    """
    if created:
        try:
            # غیرفعال کردن موقت سیگنال
            post_save.disconnect(handle_user_creation, sender=CustomUser)
            
            with transaction.atomic():
                # حذف کدهای قدیمی (در صورت وجود)
                Code.objects.filter(user=instance).delete()
                # ایجاد کد جدید
                Code.objects.create_verification_code(user=instance)
        
        except Exception as e:
            logger.error(f"Error creating verification code for user {instance.id}: {e}")
            raise
        
        finally:
            # اتصال مجدد سیگنال
            post_save.connect(handle_user_creation, sender=CustomUser)