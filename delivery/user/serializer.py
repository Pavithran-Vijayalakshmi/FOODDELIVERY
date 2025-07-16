from rest_framework import serializers
from .models import user
from orders.models import orders, Cart
from orders.serializer import OrderSerializer, CartSerializer
from restaurants.models import restaurants
from restaurants.serializer import RestaurantListSerializer



class UserSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)
    cart = CartSerializer(many=True, read_only=True)
    restaurants = serializers.SerializerMethodField()

    class Meta:
        model = user
        fields = [
            'id', 'username', 'email', 'phone', 'user_type', 'created_at',
            'orders', 'cart', 'restaurants'
        ]
        
    def get_restaurants(self, obj):
        all_restaurants = restaurants.objects.all()
        return RestaurantListSerializer(all_restaurants, many=True).data
    
    
class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = user
        fields = ['username', 'email', 'phone', 'user_type'
        ]

