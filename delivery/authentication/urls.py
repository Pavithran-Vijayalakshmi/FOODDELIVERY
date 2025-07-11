from django.urls import path,include
from .views import RegisterView, LoginView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from orders.views import CartView

urlpatterns = [
    path('restaurants/',include('restaurants.urls')),
    path('user/',include('user.urls')),
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('login/refresh/',  TokenRefreshView.as_view(), name = 'tokenrefresh'),
    path('login/cart/',CartView.as_view(),name='cart'),
    # path('accounts/',include('django.contrib.auth.urls')),
]
