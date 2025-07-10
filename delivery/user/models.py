from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid
from django.contrib.auth.models import AbstractUser

# Register your models here.
class user(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = PhoneNumberField(region='IN') 
    user_type_choices= [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    ]
    user_type = models.CharField(max_length=10,choices=user_type_choices)
    created_at = models.DateTimeField(auto_now_add=True)

