import random
from django.test import TestCase
from codes.signals import post_save_generate_code
from users.models import CustomUser
from ..models import Code
from django.utils import timezone
from datetime import  timedelta
import time
from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from concurrent.futures import ThreadPoolExecutor
import threading
from django.db import connections, transaction
from django.test import override_settings

@override_settings(
    AUTH_USER_MODEL='users.CustomUser',
    AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend']
)


class CodeModelTest(TransactionTestCase):
    def setUp(self):
        # غیرفعال کردن سیگنال‌ها در طول تست
        from django.db.models import signals
        signals.post_save.disconnect(
            receiver=post_save_generate_code,
            sender=CustomUser
        )
        
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
            phone_number='09123456789'
        )
        Code.objects.filter(user=self.user).delete()
            

    def tearDown(self):
        # اتصال مجدد سیگنال‌ها پس از تست
        from django.db.models import signals
        signals.post_save.connect(
            receiver=post_save_generate_code,
            sender=CustomUser
        )


    def test_code_creation(self):
        """تست ایجاد خودکار کد هنگام ساخت شیء"""
        code = Code.objects.create(user=self.user)
        self.assertEqual(len(code.number), 5)
        self.assertTrue(code.number.isdigit())
        self.assertFalse(code.is_used)
        self.assertIsNotNone(code.expires_at)
        self.assertGreater(code.expires_at, timezone.now())

    def test_is_valid_method(self):
        """تست متد is_valid"""
        code = Code.objects.create(user=self.user)
        
        # کد استفاده نشده و منقضی نشده
        self.assertTrue(code.is_valid())
        
        # کد استفاده شده
        code.is_used = True
        code.save()
        self.assertFalse(code.is_valid())
        
        # کد منقضی شده
        code.is_used = False
        code.expires_at = timezone.now() - timedelta(minutes=1)
        code.save()
        self.assertFalse(code.is_valid())


    def test_concurrent_code_creation(self):
        """تست ایجاد همزمان کدها برای کاربران مختلف"""
        connections.close_all()
        
        success_count = 0
        exceptions = []
        lock = threading.Lock()
        
        def create_code(i):
            nonlocal success_count
            try:
                import time  # اضافه کردن این خط
                time.sleep(random.uniform(0, 0.2))
                
                with transaction.atomic():
                    unique_id = f"{i}_{threading.get_ident()}_{time.time()}"
                    user = CustomUser.objects.create_user(
                        username=f'user_{unique_id}',
                        password='testpass123',
                        phone_number=f'09{hash(unique_id) % 1000000000:09d}'
                    )
                    code = Code.objects.create(user=user)
                    with lock:
                        success_count += 1
                    return code
            except Exception as e:
                with lock:
                    exceptions.append(str(e))
                return str(e)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_code, i) for i in range(10)]
            for future in futures:
                future.result()
        
        self.assertEqual(success_count, 10, f"خطاها: {exceptions}")
    
    
    def test_string_representation(self):
        """تست نمایش رشته‌ای مدل"""
        code = Code.objects.create(user=self.user)
        # تست نمایش پایه
        self.assertIn(f"کد {code.number} برای {self.user.username}", str(code))
        # تست نمایش با وضعیت
        self.assertIn("معتبر" if code.is_valid() else "منقضی", str(code))
    
class CodeValidationTest(TestCase):
    def test_invalid_code_length(self):
        """تست کد با طول نامعتبر"""
        user = CustomUser.objects.create_user(
            username='testuser2',
            password='testpass123',
            phone_number='09123456782'
        )
        code = Code(user=user, number='1234')  # کمتر از 5 رقم
        with self.assertRaises(ValidationError):
            code.full_clean()
            
    def test_non_digit_code(self):
        """تست کد با کاراکترهای غیرعددی"""
        user = CustomUser.objects.create_user(
            username='testuser3',
            password='testpass123',
            phone_number='09123456783'
        )
        code = Code(user=user, number='12a45')  # شامل حرف
        with self.assertRaises(ValidationError):
            code.full_clean()