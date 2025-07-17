from decimal import Decimal
from rest_framework import serializers

from coupons.models import CouponUsage
from .models import orders, Cart, OrderItem
from restaurants.serializer import MenuItemSerializer
from django.utils import timezone



class CartSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    discounted_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'menu_item', 'quantity', 'total_price', 'discounted_total']

    def get_total_price(self, obj):
        return obj.menu_item.price * obj.quantity

    def get_discounted_total(self, obj):
        total = self.get_total_price(obj)
        coupon = obj.applied_coupon

        if coupon  and coupon.start_time <= timezone.now() <= coupon.end_time:
            discount = (Decimal(coupon.discount_percent) / Decimal(100)) * total
            return (total - discount).quantize(Decimal('0.01'))

        return total



class CartCreateSerializer(serializers.ModelSerializer):
    # menu_item = MenuItemSerializer(read_only=True)
    class Meta:
        model = Cart
        fields = ['menu_item', 'quantity']
        
        
        
class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    restaurant_name = serializers.CharField(source='menu_item.restaurant.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'restaurant_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = orders
        fields = ['id', 'user', 'restaurant', 'total_amount', 'status', 'placed_at', 'delivery_address', 'order_items']

class CartItemUpdateSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'menu_item', 'quantity', 'total_price']