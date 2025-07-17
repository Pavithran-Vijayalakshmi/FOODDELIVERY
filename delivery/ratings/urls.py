from django.urls import path
from .views import RatingCreateView, RatingUpdateDeleteView

urlpatterns = [
    path('create/', RatingCreateView.as_view(), name='create-rating'),
    path('update/', RatingUpdateDeleteView.as_view(), name='update-rating'),
    path('delete/', RatingUpdateDeleteView.as_view(), name='delete-rating'),
]
