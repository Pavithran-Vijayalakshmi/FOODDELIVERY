from django.contrib import admin
from .models import Restaurant, MenuItem, Offer, Category
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

admin.site.register(Restaurant)
admin.site.register(MenuItem)
admin.site.register(Offer)
admin.site.register(Category)

