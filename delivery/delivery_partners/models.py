from django.db import models
from restaurants.models import restaurants
from user.models import user
import uuid
from django.core.validators import RegexValidator

class Delivery_Partners(models.Model):
    partner_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?\d{10,15}$', message="Enter a valid phone number")]
    )
    vehicle_number = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    assigned_restaurants = models.ManyToManyField(restaurants, related_name='delivery_partners')
    max_orders = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name
    
    def active_orders_count(self):
        return self.orders.filter(status__in=['confirmed', 'out_for_delivery']).count()
    
    def has_capacity(self):
        return self.active_orders_count() < self.max_orders

