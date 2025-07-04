from django.urls import path
from .views import restaurantsList, MenuList, orderItemsList, Ratings, CartList
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(
    'List of Restaurants', restaurantsList , basename= ' ListOfRestaurants'
)
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

urlpatterns = router.urls