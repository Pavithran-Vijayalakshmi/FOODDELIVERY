from datetime import timedelta
from django.utils import timezone
from django.db import models
import uuid
from django.conf import settings
from common.base import (AuditMixin, AddressMixin, 
                         MediaMixin, PriceMixin, 
                         StatusMixin, TimeRangeMixin,
                         ComplianceAndBankDetailsMixin,
                         RestaurantPaymentInfoMixin, BankDetailsMixin, PaymentMethodMixin, ProfileMixin)
from phonenumber_field.modelfields import PhoneNumberField
from common.types import RESTAURANT_TYPE_CHOICES, MENU_ITEM_TYPE_CHOICES


class Restaurant(AuditMixin, AddressMixin, StatusMixin,
                 ComplianceAndBankDetailsMixin, RestaurantPaymentInfoMixin,
                 BankDetailsMixin):
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_restaurants',
        default=None
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(default='')
    restaurant_primary_phone = PhoneNumberField(unique=True, region='IN')
    email = models.EmailField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open = models.BooleanField(default=True)
    restaurant_type = models.CharField(max_length=10, choices=RESTAURANT_TYPE_CHOICES, default='both')
    is_approved = models.BooleanField(default=False)

    class Meta:
        unique_together = ('name', 'city')
        unique_together = ('name', 'email')
        unique_together = ('name', 'address_line1')
        verbose_name_plural = "Restaurants"
        permissions = [
            ("can_approve_restaurant", "Can approve restaurant"),
        ]

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name


class MenuItem(AuditMixin, PriceMixin, MediaMixin):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menu_item_category')
    item_type = models.CharField(max_length=10, choices=MENU_ITEM_TYPE_CHOICES, default='both')
    is_approved = models.BooleanField(default=False)

    class Meta:
        unique_together = ('restaurant', 'name')
        permissions = [
            ("can_approve_item", "Can approve item"),
        ]

    def __str__(self):
        return self.name





    
    
class Offer(AuditMixin, StatusMixin, TimeRangeMixin):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='offers')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True, related_name='offers')
    title = models.CharField(max_length=255)
    percentage = models.DecimalField(max_digits=5, decimal_places=2) 
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  

    def __str__(self):
        return self.title