from django.test import TestCase
from users.models import CustomUser
from ..models import Code

class CodeSignalsTest(TestCase):
    def test_code_creation_on_user_creation(self):
        """تست ایجاد خودکار کد هنگام ساخت کاربر جدید"""
        # تعداد کدهای قبل از ایجاد کاربر
        initial_count = Code.objects.count()
        
        user = CustomUser.objects.create_user(
            username='newuser',
            password='testpass123',
            phone_number='09123456780'
        )
        
        # باید یک کد جدید ایجاد شده باشد
        self.assertEqual(Code.objects.count(), initial_count + 1)
        
        # کد باید به کاربر جدید مرتبط باشد
        code = Code.objects.get(user=user)
        self.assertEqual(code.user, user)
        
        # تست حذف کدهای قبلی اگر کاربر جدیدی با همان اطلاعات ایجاد شود
        # (این سناریو بستگی به منطق کسب‌وکار شما دارد)
        new_user = CustomUser.objects.create_user(
            username='newuser2',
            password='testpass123',
            phone_number='09123456781'  
        )
        self.assertEqual(Code.objects.filter(user=new_user).count(), 1)