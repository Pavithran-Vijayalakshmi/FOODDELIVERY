from django.urls import path
from .views import (UserListView,  UserCreateView,
                    MeView,
                    FavoriteCreateView,FavoriteUpdateView,FavoriteDeleteView,
                    SavedAddressListCreateView, SavedAddressUpdateDeleteView,
                    UpdateUserProfileView)

from restaurants.views import RestaurantMenuView, UserRestaurantsListView
from coupons.views import ApplyCouponView, CreateCouponView, RemoveCouponView

app_name = "user"

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('create/',UserCreateView.as_view(),name= 'user-create'),
    path('me/', MeView.as_view(), name='user-me'), 
    path('profile/update/', UpdateUserProfileView.as_view(), name='update-user-profile'),
    path('restaurant/menu/', RestaurantMenuView.as_view(), name='restaurant-menu'),
    path('favorites/create/',FavoriteCreateView.as_view(), name='create-favorite'),
    path('favorites/update/',FavoriteUpdateView.as_view(), name='create-favorite'),
    path('favorites/delete/',FavoriteDeleteView.as_view(), name='create-favorite'),
    path('addresses/add/', SavedAddressListCreateView.as_view(), name='saved-address-list-create'),
    path('addresses/', SavedAddressListCreateView.as_view(), name='saved-address-list-create'),
    path('addresses/delete/', SavedAddressUpdateDeleteView.as_view(), name='saved-address-update-delete'),
    path('addresses/update/', SavedAddressUpdateDeleteView.as_view(), name='saved-address-list-create'),
    path('coupons/apply/', ApplyCouponView.as_view(), name='apply-coupon'),
    path('createcoupon/', CreateCouponView.as_view(), name= 'create-coupon'),
    path('removecoupon/',RemoveCouponView.as_view(), name='remove-coupon'),
    
]
