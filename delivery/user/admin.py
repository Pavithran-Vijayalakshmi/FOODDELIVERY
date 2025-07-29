from django.contrib import admin
from .models import User, Favorite, SavedAddress

admin.site.register(User)
admin.site.register(Favorite)
admin.site.register(SavedAddress)