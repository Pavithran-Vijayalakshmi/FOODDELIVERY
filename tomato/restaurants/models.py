from django.db import models


# Create your models here.
class restaurantsModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
class MenuItems(models.Model):
    m_id = models.BigAutoField(primary_key=True)
    m_restaurant_id = models.ManyToManyField('restaurantsModel',related_name='item',blank=True)
    m_name = models.CharField(max_length=100)
    m_price = models.DecimalField(max_digits=10, decimal_places=2)
    m_is_available = models.BooleanField(default=True)
    m_category = models.CharField(max_length=50)
    m_created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.m_name
    
    
class rating(models.Model):
    r_id = models.BigAutoField(primary_key=True)
    r_user_id = models.ManyToManyField('user.userClass',related_name='rating1')
    r_restaurant_id = models.ManyToManyField('restaurantsModel',related_name='item1',blank=True)
    r_MenuItems_id = models.ManyToManyField('MenuItems',related_name='item_rating1')
    r_rating = models.IntegerField()
    r_review = models.TextField()
    r_created_at = models.DateTimeField(auto_now_add=True)

    
class Cart(models.Model):
    c_id = models.BigAutoField(primary_key=True)
    c_user_id = models.ManyToManyField('user.userClass',related_name='rating2')
    c_MenuItems_id = models.ManyToManyField('MenuItems',related_name='item_rating2')
    c_quantity = models.IntegerField()
    c_created_at = models.DateTimeField(auto_now_add=True)

    
class OrderItems(models.Model):
    o_id = models.BigAutoField(primary_key=True)
    o_user_id = models.ManyToManyField('user.userClass',related_name='order1')
    o_order_id = models.ManyToManyField('orders.ordersModel',related_name='orderItem1')
    o_quantity = models.IntegerField()
    o_price = models.DecimalField(max_digits=10, decimal_places=2)
