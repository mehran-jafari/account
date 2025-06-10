from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from core.helper import clean_auth_session, get_client_ip, send_verification_code
from core.settings import CODE_RESEND_TIMEOUT
from users.models import CustomUser
from django.contrib.auth import login,update_session_auth_hash
from .forms import CodeVerificationForm
from .models import Code


@require_http_methods(["GET", "POST"])
def verify_view(request):
    """Code verification view with session validation"""
    if 'pk' not in request.session:
        messages.warning(request, "Please login first")
        return redirect('users:login')

    try:
        user = CustomUser.objects.get(pk=request.session['pk'])
    except ObjectDoesNotExist:
        messages.error(request, "User not found")
        clean_auth_session(request)
        return redirect('users:login')

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
        return redirect('users:login')

    # Handle GET requests (code resend logic)
    if request.method == "GET":
        last_sent = request.session.get('last_code_sent')
        if last_sent:
            last_sent_time = timezone.datetime.fromisoformat(last_sent)
            if (timezone.now() - last_sent_time).seconds < CODE_RESEND_TIMEOUT:
                messages.info(request, "Code already sent. Please wait before requesting a new one.")
                return render(request, 'codes/verify.html', {'form': form, 'user': user})

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
            return redirect('users:login')

    return render(request, 'codes/verify.html', {'form': form, 'user': user})
 
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

    return render(request, 'codes/verify_password_change.html', {'form': form})