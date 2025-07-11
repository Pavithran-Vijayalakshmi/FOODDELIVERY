from django.urls import path,include
from .views import RegisterView, LoginView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('login/refresh/',  TokenRefreshView.as_view(), name = 'tokenrefresh')
    # path('accounts/',include('django.contrib.auth.urls')),
]
