from rest_framework import serializers
from .models import orders

class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = orders
        fields = ["total_amount","status","placed_at","delivery_address"]
        

class OrderCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = orders
        fields = ["total_amount","delivery_address"]

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user_id'] = request.user
        return orders.objects.create(**validated_data)
    
