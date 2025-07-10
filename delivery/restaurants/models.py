from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid

# Create your models here.
class restaurants(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    phone = PhoneNumberField(unique=True, region="IN")
    email = models.EmailField()
    address = models.TextField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class MenuItems(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, related_name='menu_items',null=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    
class rating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('user.user', on_delete=models.CASCADE, related_name='ratings',null=True)
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, related_name='ratings', null=True, blank=True)
    menu_item = models.ForeignKey(MenuItems, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField()
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('user.user', on_delete=models.CASCADE, related_name='cart',null=True)
    menu_item = models.ForeignKey(MenuItems, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0, null=False)
    created_at = models.DateTimeField(auto_now_add=True)


    
class OrderItems(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('user.user', on_delete=models.CASCADE,null=True)
    order = models.ForeignKey('orders.orders', on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField(default=0,null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
