from django import forms
from codes.models import Code
from django.core.exceptions import ValidationError
from users.models import CustomUser

class CodeVerificationForm(forms.Form):
    code = forms.CharField(
        max_length=5,
        min_length=5,
        widget=forms.TextInput(attrs={
            'placeholder': '12345',
            'class': 'form-control',
        }),
        label="Verification Code"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_code(self):
        code = self.cleaned_data['code']
        
        if not self.user:
            raise ValidationError("User is required for code verification")
        
        try:
            code_obj = Code.objects.get(
                number=code,
                user=self.user,
                is_used=False
            )
            
            if not code_obj.is_valid():
                raise ValidationError("This code has expired or is invalid")
                
            return code_obj
        except Code.DoesNotExist:
            raise ValidationError("Invalid verification code")
        
    class Meta:
        model = Code
        fields = ('code')
            
class RequestCodeForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'your@email.com',
            'class': 'form-control',
        }),
        label="Email Address"
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = CustomUser.objects.get(email=email)
            return user
        except CustomUser.DoesNotExist:
            raise ValidationError("No user found with this email address")





