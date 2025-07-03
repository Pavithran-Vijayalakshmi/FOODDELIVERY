from django.urls import path
from .views import restaurantsList
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(
    'List of Restaurants', restaurantsList , basename= ' ListOfRestaurants'
)


urlpatterns = [] + router.urls