from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_iranian_phone_number(value):
    """
    Validator function برای شماره تلفن ایرانی
    """
    if not value:
        return
    
    value = str(value).strip()
    
    # حذف همه فاصله‌ها و کاراکترهای غیرعددی
    cleaned = ''.join(filter(str.isdigit, value))
    
    if cleaned.startswith('98'):
        cleaned = '0' + cleaned[2:]
    elif cleaned.startswith('+98'):
        cleaned = '0' + cleaned[3:]
    
    if not cleaned.startswith('09'):
        raise ValidationError(_("شماره تلفن باید با 09 شروع شود."))
    
    if len(cleaned) != 11:
        raise ValidationError(_("شماره تلفن باید 11 رقم باشد."))
    
    return cleaned
