from rest_framework import serializers
from .models import User, Favorite, SavedAddress
from orders.models import Cart
from orders.serializer import OrderSerializer, CartSerializer
from restaurants.models import Restaurant, MenuItem
from restaurants.serializer import  RestaurantDetailSerializer, MenuItemSerializer
from decimal import Decimal




class UserSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)
    cart = serializers.SerializerMethodField()
    restaurants = serializers.SerializerMethodField()
    favorites = serializers.SerializerMethodField()
    menu_items =serializers.SerializerMethodField()
    saved_addresses= serializers.SerializerMethodField()
    

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'user_type', 'created_at',
            'orders', 'cart', 'restaurants','menu_items', 'favorites','saved_addresses',
        ]
        
    def get_cart(self, obj):
        cart_items = Cart.objects.filter(user=obj).select_related('menu_item__restaurant')
        grouped = {}

        for item in cart_items:
            restaurant = item.menu_item.restaurant
            rest_id = restaurant.id

            if rest_id not in grouped:
                grouped[rest_id] = {
                    "restaurant_id": rest_id,
                    "restaurant_name": restaurant.name,
                    "items": [],
                    "total": Decimal("0.00")
                }

            item_data = CartSerializer(item, context=self.context).data
            grouped[rest_id]["items"].append(item_data)

            discounted_total = Decimal(item_data.get("discounted_total", "0.00"))
            grouped[rest_id]["total"] += discounted_total

        for group in grouped.values():
            group["total"] = round(group["total"], 2)

        return list(grouped.values())
    
    def get_restaurants(self, obj):
        all_restaurants = Restaurant.objects.all()
        return RestaurantDetailSerializer(all_restaurants, many=True).data

    def get_favorites(self, obj):
        favorites_qs = Favorite.objects.filter(user=obj)
        return FavoriteSerializer(favorites_qs, many=True).data
    
    def get_menu_items(self, obj):
        if obj.user_type != 'customer':
            return [] 
        menu_items = MenuItem.objects.all().select_related('restaurant')
        return MenuItemSerializer(menu_items, many=True).data
    
    def get_saved_addresses(self, obj):
        saved_addresses = SavedAddress.objects.filter(user=obj)
        return SavedAddressSerializer(saved_addresses, many=True).data
    
    
class UserCreateSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'user_type'
        ]
        
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    dob = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    class Meta:
        model = User
        fields = [
            'name', 'email', 'phone', 'dob', 'gender', 'profile_picture',
            'address_line1', 'address_line2', 'city', 'state', 'pincode', 'country','label',
        ]
        extra_kwargs = {
            'email': {'required': False},
            'phone': {'required': False},
        }

    def update(self, instance, validated_data):
        label = validated_data.pop('label', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        address_fields = ['address_line1', 'address_line2', 'city', 'state', 'pincode', 'country']
        address_data = {field: getattr(instance, field) for field in address_fields if getattr(instance, field, None)}
        
        if label and address_data:
            saved_address, created = SavedAddress.objects.update_or_create(
                user=instance,
                label=label,
                defaults={**address_data}
            )

        return instance

class FavoriteSerializer(serializers.ModelSerializer):
    restaurant = RestaurantDetailSerializer(read_only=True)
    menu_item = MenuItemSerializer(read_only=True)
    class Meta:
        model = Favorite
        fields = ['id', 'restaurant', 'menu_item', 'created_at']
        read_only_fields = ['id', 'created_at']
        
        
class SavedAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedAddress
        fields = ['id', 'label', 'address_line1', 'address_line2', 'city', 'state', 'pincode', 'country', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']