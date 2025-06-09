from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import (
    home_view, auth_view, logout_view, verify_view,
    register_view, profile_view, profile_edit_view,
    password_change_view, verify_password_change_view
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('', home_view, name='home'),
    path('login/', auth_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify/', verify_view, name='verify'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('change-password/', password_change_view, name='password_change'),
    path('verify-password-change/', verify_password_change_view, name='verify_password_change'),
]

# Add debug toolbar and static/media files in debug mode
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler403 = 'core.errors.handler403'
handler404 = 'core.errors.handler404'
handler500 = 'core.errors.handler500'


