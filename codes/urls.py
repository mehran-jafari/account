from django.urls import path
from . import views

app_name = 'codes'

urlpatterns = [
    path('verify/', views.verify_view, name='verify'),
    path('verify-password-change/', views.verify_password_change_view, name='verify_password_change'),
]