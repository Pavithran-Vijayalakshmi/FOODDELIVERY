from django.urls import path
from .views import RegionListView

urlpatterns = [
    path('api/regions/', RegionListView.as_view(), name='region-list'),
]