from django.urls import path
from .views import login_view, register_view, dashboard_view, logout_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),  # Делаем dashboard главной страницей
    path('login/', login_view, name='login'),  # Login page
    path('register/', register_view, name='register'),  # Registration page
    path('logout/', logout_view, name='logout'),
]
