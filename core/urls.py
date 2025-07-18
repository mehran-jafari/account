from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import home_view




urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('codes/', include('codes.urls')),
    path('users/', include('users.urls')),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler403 = 'core.errors.handler403'
handler404 = 'core.errors.handler404'
handler500 = 'core.errors.handler500'