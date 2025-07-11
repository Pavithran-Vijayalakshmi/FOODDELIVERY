from rest_framework import serializers
from .models import restaurants, MenuItems, rating,Cart,OrderItems

class restaurantsSerializer(serializers.ModelSerializer):
    class Meta:
        model = restaurants
        fields = ["name","phone","email","address","opening_time","closing_time","is_open"]
        
class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItems
        fields = '__all__'
        
class ratingSerializer(serializers.ModelSerializer):
    class Meta:
        model = rating
        fields = '__all__'
        
class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'
        
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItems
        fields = '__all__'

