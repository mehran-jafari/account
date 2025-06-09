from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from users.validator import validate_iranian_phone_number
from django.conf import settings


class CustomUser(AbstractUser):
    phone_number = models.CharField(
        max_length=11,
        unique=True,
        validators=[validate_iranian_phone_number],
        blank=False,
        null=False,
        verbose_name=_("شماره تلفن"),
        help_text=_("با 09 شروع شود و 11 رقم باشد. مثال: 09123456789")
    )
    
    # Security fields
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    def clean(self):
        super().clean()
        if self.phone_number:
            self.phone_number = validate_iranian_phone_number(self.phone_number)
    
    def is_account_locked(self):
        return (
            self.account_locked_until and 
            self.account_locked_until > timezone.now()
        )
    
    def reset_login_attempts(self):
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()
    
    def increment_failed_attempt(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            self.account_locked_until = timezone.now() + timezone.timedelta(
                minutes=settings.ACCOUNT_LOCKOUT_MINUTES
            )
        self.save()
    
    def __str__(self):
        return self.username