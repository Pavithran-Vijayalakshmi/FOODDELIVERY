from django.urls import path

from common.views import RegionListView
from .views import (RegisterView, LoginView, 
                    LogoutView, CustomTokenObtainPairView, 
                    RestaurantRegisterView,DeliveryPersonLogoutView,
                    AdminLoginView, DeliveryPartnerRegisterView,
                    DeliveryPersonRegisterView, AdminRegisterView)
from django.views.generic import TemplateView



from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

app_name = "authentication"

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/restaurant/register/',RestaurantRegisterView.as_view(), name = 'restaurant_signup'),
    path('api/delivery_partner/register/',DeliveryPartnerRegisterView.as_view(), name = 'delivery_parnter'),
    path('api/delivery_person/register/',DeliveryPersonRegisterView.as_view(), name = 'delivery_person'),
    path('api/admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('api/admin/register/', AdminRegisterView.as_view(), name = "admin-register"),
    path('api/regions/', RegionListView.as_view(), name='region-list'),
    path('api/deliveryperson/logout/',DeliveryPersonLogoutView.as_view(), name='delivery-person-logout'),
    
]
