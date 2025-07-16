from django.db import models
from user.models import user
from restaurants.models import restaurants
from orders.models import MenuItem

class rating(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ('user', 'restaurant'),
            ('user', 'menu_item'),
        ]
