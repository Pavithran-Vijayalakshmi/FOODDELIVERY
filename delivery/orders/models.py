from django.db import models
from user.models import user
from restaurants.models import restaurants, MenuItem
from coupons.models import Coupon
from delivery_partners.models import Delivery_Partners
import uuid

class Cart(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name='cart')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    applied_coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)


    def __str__(self):
        return f"{self.user.username} - {self.menu_item.name}"


class orders(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name='orders', null=True)
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, null=True)
    delivery_partner = models.ForeignKey(Delivery_Partners, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    placed_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.TextField()
    restaurant_ready = models.BooleanField(default=False)
    picked_by_partner = models.BooleanField(default=False)
    delivered_to_user = models.BooleanField(default=False)
    cancelled_reason = models.TextField(null=True, blank=True)
    
    def cancel(self):
        self.status = 'cancelled'
        self.save()


    # def save(self, status):
    #         self.status = status
            
    def assign_delivery_partner(self):
        available_partners = self.restaurant.delivery_partners.all()
        for partner in available_partners:
            if partner.has_capacity():
                self.delivery_partner = partner
                self.save()
                break

    def __str__(self):
        return f"Order #{self.pk} - {self.user.username}"



class OrderItem(models.Model):
    order = models.ForeignKey(orders, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
