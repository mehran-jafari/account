from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, 
    UserChangeForm, 
    PasswordChangeForm,
    AuthenticationForm
)
from users.models import CustomUser
from django.core.exceptions import ValidationError
import time





class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            try:
                user = CustomUser.objects.get(username=username)
                if user.is_account_locked():
                    raise ValidationError(
                        "حساب شما موقتاً قفل شده است. لطفاً بعداً تلاش کنید."
                    )
            except CustomUser.DoesNotExist:
                pass
        
        return super().clean()


class CustomRegisterForm(UserCreationForm):
    
    honeypot = forms.CharField(
        required=False,
        label='',
        widget=forms.HiddenInput()
    )
    
    def clean_honeypot(self):
        honeypot = self.cleaned_data.get('honeypot')
        if honeypot:
            raise ValidationError("Bot detected")
        return honeypot
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number')
        

class ProfileEditForm(UserChangeForm):
    password = None  # حذف فیلد رمز عبور از فرم

    class Meta:
        model = CustomUser
        fields = ('username','first_name','last_name','email')

class CustomPasswordChangeForm(PasswordChangeForm):
    pass
