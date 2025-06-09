from django.urls import path
from . import views

urlpatterns = [
    path('', views.code_home, name='code_home'),
]
