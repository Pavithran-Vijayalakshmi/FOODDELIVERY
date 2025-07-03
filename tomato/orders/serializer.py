from rest_framework import serializers
from .models import ordersModel

class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ordersModel
        fields = '__all__'
