from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    
    path('login/', views.auth_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('change-password/', views.password_change_view, name='password_change'),
]