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
from django.conf import settings

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
