from rest_framework import serializers
from .models import user
from orders.serializer import OrdersSerializer

class userSerializer(serializers.ModelSerializer):
    orders = OrdersSerializer(many=True, read_only=True)
    class Meta:
        model = user        
        fields = ['name', 'email', 'phone', 'user_type', 'created_at', 'orders']
    