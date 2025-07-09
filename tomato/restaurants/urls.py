from django.urls import path
from .views import restaurantsList, MenuList, orderItemsList, Ratings, CartList
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(
    'menu-items', MenuList, basename='menuitems'
)
router.register(
    'order-items', orderItemsList, basename='orderitems'
)
router.register(
    'ratings', Ratings, basename='ratings'
)
router.register(
    'cart', CartList, basename='cart'
)

urlpatterns = [
    path('ListofRestaurants/', restaurantsList.as_view() ,name = ' List Of Restaurants')
    ]+router.urls