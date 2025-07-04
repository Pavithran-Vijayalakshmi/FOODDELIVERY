from django.db import models
from user.models import userClass


class ordersModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    total_amount = models.DecimalField(max_digits= 10 , decimal_places= 2)
    options = [
        ('pending', 'Pending'), 
        ('confirmed','Confirmed'),
        ('preparing','Preparing'),
        ('out_for_delivery','Out_for_Delivery'),
        ('delivered','Delivered'),
        ('cancelled','Cancelled'),]
    status = status = models.CharField(max_length=20, choices=options, default='pending')
    placed_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.TextField()
    user_id = models.ForeignKey(userClass, on_delete=models.CASCADE, related_name='orders')
    restaurant_id = models.ManyToManyField('restaurants.restaurantsModel', related_name='order')
