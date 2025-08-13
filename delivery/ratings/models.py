from django.db import models
from user.models import User
from delivery import settings
from restaurants.models import Restaurant
from orders.models.models import MenuItem
from common.base import AuditMixin

class Rating(AuditMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'restaurant'], name='unique_user_restaurant_rating'),
            models.UniqueConstraint(fields=['user', 'menu_item'], name='unique_user_menuitem_rating'),
        ]

    def __str__(self):
        if self.restaurant:
            return f"{self.user} rated {self.restaurant.name}: {self.rating}"
        elif self.menu_item:
            return f"{self.user} rated {self.menu_item.name}: {self.rating}"
        return f"{self.user} rating: {self.rating}"
