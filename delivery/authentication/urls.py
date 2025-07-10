from django.urls import path,include
from .views import LoginView

urlpatterns = [
    path('signup/',LoginView, name = "signup" ),
    path('accounts/',include('django.contrib.auth.urls')),
]
