from django.db import models

# Register your models here.
class userClass(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    password = models.TextField()
    user_type_choices= [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    ]
    user_type = models.CharField(max_length=10,choices=user_type_choices)
    created_at = models.DateTimeField(auto_now_add=True)

