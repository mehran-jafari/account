import requests
from django.conf import settings
from urllib.parse import quote
import hmac
import hashlib
import time

class RemotePost:
    def __init__(self, username=None, password=None, footer=None):
        sms_config = getattr(settings, 'SMS_CONFIG', {})
        self.username = username or sms_config.get('USERNAME', '')
        self.password = password or sms_config.get('PASSWORD', '')
        self.footer = footer or sms_config.get('FOOTER', '')
        self.api_key = sms_config.get('API_KEY', '')
        self.base_url = sms_config.get('BASE_URL', 'http://smspanel.Trez.ir/')
    
    
    def _generate_signature(self, params):
        """Generate HMAC signature for API requests"""
        sorted_params = '&'.join(f"{k}={quote(str(v))}" for k, v in sorted(params.items()))
        return hmac.new(
            self.api_key.encode(),
            sorted_params.encode(),
            hashlib.sha256
        ).hexdigest()

    def _make_request(self, endpoint, data):
        """Secure request method with timeout and signature"""
        url = f"{self.base_url.rstrip('/')}/{endpoint}"
        data['Timestamp'] = int(time.time())
        data['Signature'] = self._generate_signature(data)
        
        try:
            response = requests.post(
                url,
                data=data,
                timeout=5,
                verify=True  # Enable SSL verification
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"[SMS ERROR] Request failed: {e}")
            return None

    def send_code(self, mobile_number, footer):
        data = {
            'Username': self.username,
            'Password': self.password,
            'Mobile': mobile_number,
            'Footer': footer,
        }
        return self._make_request("AutoSendCode.ashx", data)
        try:
            response = requests.post(url, data=data, timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"[SMS ERROR] ارسال کد شکست خورد: {e}")
            return None

    def is_code_valid(self, mobile_number, code):
        url = "http://smspanel.Trez.ir/CheckSendCode.ashx"
        data = {
            'Username': self.username,
            'Password': self.password,
            'Mobile': mobile_number,
            'Code': code,
        }
        try:
            response = requests.post(url, data=data, timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"[SMS ERROR] بررسی کد شکست خورد: {e}")
            return None

    def send_custom_message(self, mobile_number, message):
        url = "http://smspanel.Trez.ir/SendMessageWithCode.ashx"
        data = {
            'Username': self.username,
            'Password': self.password,
            'Mobile': mobile_number,
            'Message': message,
        }
        try:
            response = requests.post(url, data=data, timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"[SMS ERROR] ارسال پیامک سفارشی شکست خورد: {e}")
            return None