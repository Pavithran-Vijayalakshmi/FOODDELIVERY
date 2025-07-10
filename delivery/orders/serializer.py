from rest_framework import serializers
from .models import orders

class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = orders
        fields = '__all__'
