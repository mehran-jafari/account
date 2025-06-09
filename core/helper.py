# core/helpers.py
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from .utils import RemotePost
import logging

# Set up logging
logger = logging.getLogger(__name__)

def send_verification_code(user, code):
    """
    Send verification code via SMS with rate limiting
    Args:
        user: User object with phone_number
        code: Verification code to send
    Returns:
        bool: True if SMS was sent successfully, False otherwise
    """
    try:
        # Get SMS configuration from settings
        sms_config = getattr(settings, 'SMS_CONFIG', {})
        sms_username = sms_config.get('USERNAME', '')
        sms_password = sms_config.get('PASSWORD', '')
        sms_footer = sms_config.get('FOOTER', 'Your Company')
        
        if not all([sms_username, sms_password]):
            logger.error("SMS credentials not configured")
            return False

        sms = RemotePost()
        footer_with_code = f"{sms_footer}\nکد: {code}"
        cache_key = f"sms_rate_limit_{user.phone_number}"

        # Rate limiting check
        if cache.get(cache_key):
            logger.warning(f"SMS rate limited for {user.phone_number}")
            return False

        # Send SMS
        result = sms.send_code(user.phone_number, footer_with_code)
        
        try:
            if result and int(result) > 2000:
                logger.info(f"SMS sent to {user.phone_number} | Transaction ID: {result}")
                cache.set(cache_key, True, 60)  # 1 minute rate limit
                return True
            else:
                logger.error(f"SMS failed for {user.phone_number}. Response: {result}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid server response: {result} | Error: {str(e)}")
            return False

    except Exception as e:
        logger.exception(f"Error in send_verification_code: {str(e)}")
        return False

def clean_auth_session(request):
    """
    Clean authentication-related session data
    Args:
        request: Django request object
    """
    session_keys = [
        'pk', 'auth_attempts', 'last_code_sent', 
        'password_change_user_pk', 'new_password',
        'password_change_code_sent'
    ]
    for key in session_keys:
        if key in request.session:
            del request.session[key]

def handle_failed_attempt(request):
    """
    Handle failed login attempts with rate limiting
    Args:
        request: Django request object
    Returns:
        bool: True if rate limit exceeded, False otherwise
    """
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    cache_key = f"login_attempts_{ip_address}"
    
    try:
        attempts = cache.get(cache_key, 0) + 1
        cache.set(
            cache_key, 
            attempts, 
            timeout=getattr(settings, 'LOGIN_ATTEMPT_TIMEOUT', 300)
        )

        max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
        if attempts >= max_attempts:
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            messages.error(request, "Too many attempts. Please try again later.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error in handle_failed_attempt: {str(e)}")
        return False
    
    
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
