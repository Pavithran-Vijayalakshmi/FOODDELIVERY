from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(restaurantsModel)
admin.site.register(MenuItems)
admin.site.register(rating)
admin.site.register(Cart)
admin.site.register(OrderItems)