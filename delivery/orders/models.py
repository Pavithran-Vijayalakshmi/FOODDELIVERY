from django.db import models
from user.models import User
from restaurants.models import Restaurant, MenuItem
from coupons.models import Coupon
from delivery_partners.models import Delivery_Partners, DeliveryPerson
from common.types import STATUS_CHOICES
from delivery.settings import AUTH_USER_MODEL
from common.base import AuditMixin, StatusMixin,PaymentMethodMixin
User = AUTH_USER_MODEL
import uuid

class Cart(AuditMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    applied_coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('user', 'menu_item')
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.user.username} - {self.menu_item.name} x {self.quantity}"


class Orders(AuditMixin, StatusMixin, PaymentMethodMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, related_name='orders')
    delivery_partner = models.ForeignKey(Delivery_Partners, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    order_code = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)


    def cancel(self, reason=None):
        self.status = 'cancelled'
        self.save()

    def assign_delivery_partner(self):
        if self.restaurant:
            available_partners = self.restaurant.delivery_partners.all()
            for partner in available_partners:
                if partner.has_capacity():
                    self.delivery_partner = partner
                    self.save()
                    break

    def __str__(self):
        return f"Order #{self.pk} - {self.user.username if self.user else 'Guest'}"



class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
