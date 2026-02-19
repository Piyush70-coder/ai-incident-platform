from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.company_settings_view, name='company_settings'),
    path('users/', views.company_users_view, name='company_users'),
]
