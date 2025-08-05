from django.contrib import admin
from .models import User, Favorite, SavedAddress
from common.base import City,Country,Region,State,AuditMixinAdmin


admin.site.register(User)
admin.site.register(Favorite)
admin.site.register(SavedAddress)

