
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from codes.forms import CodeVerificationForm
from .helper import clean_auth_session, get_client_ip, handle_failed_attempt, send_verification_code
from users.models import CustomUser
from codes.models import Code
from users.forms import (CustomRegisterForm, 
                        ProfileEditForm, 
                        CustomPasswordChangeForm)



# Constants
CODE_RESEND_TIMEOUT = getattr(settings, 'CODE_RESEND_TIMEOUT', 60)
MAX_LOGIN_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)


@login_required
def home_view(request):
    """Protected home view"""
    return render(request, 'main.html')


@csrf_protect
@require_http_methods(["GET", "POST"])
def auth_view(request):
    """Authentication view with rate limiting"""
    if request.user.is_authenticated:
        return redirect('home')

    form = AuthenticationForm()
    
    # Rate limiting check
    if request.session.get('auth_attempts', 0) >= MAX_LOGIN_ATTEMPTS:
        messages.error(request, "Too many attempts. Please try again later.")
        return render(request, 'auth.html', {'form': form})

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            try:
                # Delete existing unused codes in a single query
                Code.objects.filter(user=user, is_used=False).delete()
                
                # Create and send new code
                code = Code.objects.create(user=user)
                send_verification_code(user, code.number)
                
                # Store minimal session data
                request.session['pk'] = user.pk
                request.session['last_code_sent'] = timezone.now().isoformat()
                print(code)
                return redirect('verify')
            
            except Exception as e:
                messages.error(request, "Error generating verification code")
                if settings.DEBUG:
                    print(f"Error: {str(e)}")
        else:
            if handle_failed_attempt(request):
                return redirect('login')
            messages.error(request, "Invalid credentials")

    return render(request, 'auth.html', {'form': form})

def verify_view(request):
    """Code verification view with session validation"""
    if 'pk' not in request.session:
        messages.warning(request, "Please login first")
        return redirect('login')

    try:
        user = CustomUser.objects.get(pk=request.session['pk'])
    except ObjectDoesNotExist:
        messages.error(request, "User not found")
        clean_auth_session(request)
        return redirect('login')

    form = CodeVerificationForm(user=user, data=request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        code_obj = form.cleaned_data['code']
        if code_obj.is_valid():
            code_obj.mark_as_used()
            login(request, user)
            
            user.last_login_ip = get_client_ip(request)
            user.last_login_at = timezone.now()
            user.reset_login_attempts()
            user.save()
            
            
            clean_auth_session(request)
            messages.success(request, "Successfully logged in!")
            return redirect('home')
        messages.error(request, "Invalid or expired code")
        return redirect('login')

    # Handle GET requests (code resend logic)
    if request.method == "GET":
        last_sent = request.session.get('last_code_sent')
        if last_sent:
            last_sent_time = timezone.datetime.fromisoformat(last_sent)
            if (timezone.now() - last_sent_time).seconds < CODE_RESEND_TIMEOUT:
                messages.info(request, "Code already sent. Please wait before requesting a new one.")
                return render(request, 'verify.html', {'form': form, 'user': user})

        try:
            code = Code.objects.filter(
                user=user,
                is_used=False,
                expires_at__gt=timezone.now()
            ).latest('created_at')
            send_verification_code(user, code.number)
            request.session['last_code_sent'] = timezone.now().isoformat()
            messages.info(request, "Verification code sent")
        except Code.DoesNotExist:
            messages.error(request, "No valid code found")
            return redirect('login')

    return render(request, 'verify.html', {'form': form, 'user': user})

def logout_view(request):
    """Logout view with session cleanup"""
    logout(request)
    clean_auth_session(request)
    messages.success(request, "Successfully logged out")
    return redirect('home')

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')

    form = CustomRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Registration successful. Please login.")
        return redirect('login')
    return render(request, 'register.html', {'form': form})

@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'profile.html', {'user': request.user})

@login_required
def profile_edit_view(request):
    """Profile editing view"""
    form = ProfileEditForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')
    return render(request, 'profile_edit.html', {'form': form})

@login_required
def password_change_view(request):
    """Password change view with rate limiting"""
    form = CustomPasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == "GET":
        last_sent = request.session.get('password_change_code_sent')
        if last_sent:
            last_sent_time = timezone.datetime.fromisoformat(last_sent)
            if (timezone.now() - last_sent_time).seconds < CODE_RESEND_TIMEOUT:
                messages.warning(request, "Code already sent. Please wait before requesting a new one.")
                return redirect('verify_password_change')

    if request.method == "POST" and form.is_valid():
        request.session['new_password'] = form.cleaned_data['new_password1']
        Code.objects.filter(user=request.user, is_used=False).delete()
        code = Code.objects.create(user=request.user)
        send_verification_code(request.user, code.number)

        request.session['password_change_user_pk'] = request.user.pk
        request.session['password_change_code_sent'] = timezone.now().isoformat()
        messages.info(request, "Verification code sent")
        print(code)
        return redirect('verify_password_change')

    return render(request, 'password_change.html', {'form': form})

@login_required
def verify_password_change_view(request):
    """Password change verification view"""
    pk = request.session.get('password_change_user_pk')
    new_password = request.session.get('new_password')

    if not pk or not new_password:
        messages.error(request, "Invalid request")
        return redirect('password_change')

    try:
        user = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found")
        return redirect('password_change')

    form = CodeVerificationForm(user=user, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        code_obj = form.cleaned_data['code']
        if code_obj.is_valid():
            code_obj.mark_as_used()
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            clean_auth_session(request)
            request.session.pop('new_password', None)
            request.session.pop('password_change_user_pk', None)
            messages.success(request, "Password changed successfully.")
            return redirect('profile')
        messages.error(request, "Invalid or expired code.")

    return render(request, 'verify_password_change.html', {'form': form})

