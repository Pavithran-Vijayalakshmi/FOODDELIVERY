# from django.db import models
# from phonenumber_field.modelfields import PhoneNumberField
# import uuid
# from django.contrib.auth.models import AbstractUser

# # Register your models here.
# class user(AbstractUser):
#     uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100)
#     email = models.EmailField()
#     phone = PhoneNumberField(region='IN')
#     user_type_choices= [
#         ('customer', 'Customer'),
#         ('admin', 'Admin'),
#     ]
#     user_type = models.CharField(max_length=10,choices=user_type_choices)
#     created_at = models.DateTimeField(auto_now_add=True)


import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from restaurants.models import restaurants,MenuItem
from django.core.exceptions import ValidationError
from django.db.models import Q




class user(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(unique=True, region='IN')
    

    USER_TYPE_CHOICES = (
    ('Customer', 'Customer'),
    ('RestaurantOwner', 'RestaurantOwner'),
    ('admin', 'Admin'),
)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='Customer')
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ['name','email', 'phone', 'user_type']
    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username
    
    
class favorite(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name = 'favorites')
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.restaurant and self.menu_item:
            raise ValidationError("Only one of restaurant or menu_item should be set.")
        if not self.restaurant and not self.menu_item:
            raise ValidationError("One of restaurant or menu_item must be set.")

    def save(self, *args, **kwargs):
        self.full_clean()  # ensures clean() is called before saving
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

class SavedAddress(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name='saved_addresses')
    label = models.CharField(max_length=50, help_text='e.g., Home, Work')
    address = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} - {self.user.username}"



