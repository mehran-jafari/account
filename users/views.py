from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib import messages

from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from codes.models import Code
from core.helper import clean_auth_session, handle_failed_attempt, send_verification_code
from core.settings import CODE_RESEND_TIMEOUT, MAX_LOGIN_ATTEMPTS

from .forms import CustomRegisterForm, ProfileEditForm, CustomPasswordChangeForm





@csrf_protect
@require_http_methods(["GET", "POST"])
def auth_view(request):
    if request.user.is_authenticated: 
        return redirect('home')

    form = AuthenticationForm()
    
    if request.session.get('auth_attempts', 0) >= MAX_LOGIN_ATTEMPTS:
        messages.error(request, "Too many attempts. Please try again later.")
        return render(request, 'users/auth.html', {'form': form})

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            try:
                Code.objects.filter(user=user, is_used=False).delete()
                code = Code.objects.create(user=user)
                send_verification_code(user, code.number)
                
                request.session['pk'] = user.pk
                request.session['last_code_sent'] = timezone.now().isoformat()
                return redirect('codes:verify')
            
            except Exception as e:
                messages.error(request, "Error generating verification code")
                if settings.DEBUG:
                    print(f"Error: {str(e)}")
        else:
            if handle_failed_attempt(request):
                return redirect('users:login')
            messages.error(request, "Invalid credentials")

    return render(request, 'users/auth.html', {'form': form})

def logout_view(request):
    logout(request)
    clean_auth_session(request)
    messages.success(request, "Successfully logged out")
    return redirect('home')

def register_view(request):
    if request.user.is_authenticated:
       return redirect('home')

    form = CustomRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Registration successful. Please login.")
        return redirect('users:login')
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def profile_edit_view(request):
    form = ProfileEditForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('users:profile')
    return render(request, 'users/profile_edit.html', {'form': form})

@login_required
def password_change_view(request):
    form = CustomPasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == "GET":
        last_sent = request.session.get('password_change_code_sent')
        if last_sent:
            last_sent_time = timezone.datetime.fromisoformat(last_sent)
            if (timezone.now() - last_sent_time).seconds < CODE_RESEND_TIMEOUT:
                messages.warning(request, "Code already sent. Please wait before requesting a new one.")
                return redirect('codes:verify_password_change')

    if request.method == "POST" and form.is_valid():
        request.session['new_password'] = form.cleaned_data['new_password1']
        Code.objects.filter(user=request.user, is_used=False).delete()
        code = Code.objects.create(user=request.user)
        send_verification_code(request.user, code.number)

        request.session['password_change_user_pk'] = request.user.pk
        request.session['password_change_code_sent'] = timezone.now().isoformat()
        messages.info(request, "Verification code sent")
        return redirect('codes:verify_password_change')

    return render(request, 'users/password_change.html', {'form': form})