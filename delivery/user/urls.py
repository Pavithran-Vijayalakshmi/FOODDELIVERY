from django.urls import path
from .views import (UserListCreateView,
                    MeView,
                    FavoriteCreateView,FavoriteUpdateView,FavoriteDeleteView,
                    SavedAddressListCreateView, SavedAddressUpdateDeleteView,
                    UpdateUserProfileView,AdminUserListView, AdminUserCreateView, 
                    RestaurantListView)

from restaurants.views import RestaurantMenuView, UserRestaurantsListView
from coupons.views import ApplyCouponView, CreateCouponView, RemoveCouponView, CouponListView

app_name = "user"

urlpatterns = [
    path('admin/users/', AdminUserListView.as_view(), name='admin-users-list'),
    path('admin/users/create/', AdminUserCreateView.as_view(), name='admin-users-create'),
]

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user-list'),
    path('create/',UserListCreateView.as_view(),name= 'user-create'),
    path('logged_in_user_profile/', MeView.as_view(), name='user-me'), 
    path('profile/update/', UpdateUserProfileView.as_view(), name='update-user-profile'),
    path('restaurant_list/', RestaurantListView.as_view(), name ='restaurant-list'),
    path('restaurant/menu/', RestaurantMenuView.as_view(), name='restaurant-menu'),
    path('favorites/create/',FavoriteCreateView.as_view(), name='create-favorite'),
    path('favorites/update/',FavoriteUpdateView.as_view(), name='create-favorite'),
    path('favorites/delete/',FavoriteDeleteView.as_view(), name='create-favorite'),
    path('addresses/list-add/', SavedAddressListCreateView.as_view(), name='saved-address-list-create'),
    path('addresses/update_delete/', SavedAddressUpdateDeleteView.as_view(), name='saved-address-update-delete'),
    
    path('coupons/apply/', ApplyCouponView.as_view(), name='apply-coupon'),
    path('createcoupon/', CreateCouponView.as_view(), name= 'create-coupon'),
    path('removecoupon/',RemoveCouponView.as_view(), name='remove-coupon'),
    path('coupon_list/', CouponListView.as_view(), name = 'coupon-list')
    
]
