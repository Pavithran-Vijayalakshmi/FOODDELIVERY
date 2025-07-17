from datetime import timedelta
from django.utils import timezone
from django.db import models
import uuid
from django.conf import settings

class restaurants(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_restaurants',default= None
    )    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100,default=None)
    description = models.TextField(default='')
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'city')
        verbose_name_plural = "Restaurants"
        
    def __str__(self):
        return self.id


class MenuItem(models.Model):
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    category = models.CharField(max_length=50)
    image_url = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('restaurant', 'name')


    def __str__(self):
        return self.name


class Offer(models.Model):
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, related_name='offers')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True, related_name='offers')
    title = models.CharField(max_length=255)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # only percentage discount
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now() + timedelta(days=1))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title