import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from restaurants.models import Restaurant,MenuItem
from django.core.exceptions import ValidationError
from django.db.models import Q
from coupons.models import Coupon
from common.base import AuditMixin, AddressMixin, ProfileMixin, BankDetailsMixin
from common import types
from datetime import date

class User(AbstractUser, AuditMixin, AddressMixin, ProfileMixin, BankDetailsMixin):
    
    user_type = models.CharField(max_length=20, choices=types.USER_TYPE_CHOICES, default='customer')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
       

    REQUIRED_FIELDS = ['name','email', 'phone', 'user_type']
    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        if self.dob:
            today = date.today()
            self.age = (
                today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
            )
        super().save(*args, **kwargs)
    
    
class Favorite(AuditMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        if self.restaurant and self.menu_item:
            raise ValidationError("Only one of restaurant or menu_item should be set.")
        if not self.restaurant and not self.menu_item:
            raise ValidationError("One of restaurant or menu_item must be set.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'restaurant'], name='unique_user_restaurant_favorite'),
            models.UniqueConstraint(fields=['user', 'menu_item'], name='unique_user_menu_item_favorite'),
            models.CheckConstraint(
                check=(
                    (Q(restaurant__isnull=True) & Q(menu_item__isnull=False)) |
                    (Q(restaurant__isnull=False) & Q(menu_item__isnull=True))
                ),
                name='only_one_of_menu_or_restaurant'
            )
        ]

class SavedAddress(AuditMixin, AddressMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_addresses')
    label = models.CharField(max_length=50, help_text='e.g., Home, Work')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} - {self.user.username}"







    