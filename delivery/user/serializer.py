from rest_framework import serializers
from .models import user, favorite, SavedAddress
from orders.models import orders, Cart
from orders.serializer import OrderSerializer, CartSerializer
from restaurants.models import restaurants, MenuItem
from restaurants.serializer import RestaurantListSerializer, RestaurantDetailSerializer, MenuItemSerializer



class UserSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)
    cart = CartSerializer(many=True, read_only=True)
    restaurants = serializers.SerializerMethodField()
    favorites = serializers.SerializerMethodField()
    menu_items =serializers.SerializerMethodField()

    class Meta:
        model = user
        fields = [
            'id', 'username', 'email', 'phone', 'user_type', 'created_at',
            'orders', 'cart', 'restaurants','menu_items', 'favorites','saved_addresses',
        ]

    def get_restaurants(self, obj):
        all_restaurants = restaurants.objects.all()
        return RestaurantDetailSerializer(all_restaurants, many=True).data

    def get_favorites(self, obj):
        favorites_qs = favorite.objects.filter(user=obj)
        return FavoriteSerializer(favorites_qs, many=True).data
    
    def get_menu_items(self, obj):
        if obj.user_type != 'Customer':
            return [] 
        menu_items = MenuItem.objects.all().select_related('restaurant')
        return MenuItemSerializer(menu_items, many=True).data
    
    
class UserCreateSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = user
        fields = ['username', 'email', 'phone', 'user_type'
        ]

class FavoriteSerializer(serializers.ModelSerializer):
    restaurant = RestaurantDetailSerializer(read_only=True)
    menu_item = MenuItemSerializer(read_only=True)
    class Meta:
        model = favorite
        fields = ['id', 'restaurant', 'menu_item', 'created_at']
        read_only_fields = ['id', 'created_at']
        
        
class SavedAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedAddress
        fields = ['id', 'label', 'address', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']