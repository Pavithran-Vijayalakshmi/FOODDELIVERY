from django.urls import path,include
from .views import LoginView, home

app_name = 'authentication'

urlpatterns = [
    path('restaurants/',home, name = 'home'),
    path('signup/',LoginView, name = "signup" ),
    path('accounts/',include('django.contrib.auth.urls')),
]
