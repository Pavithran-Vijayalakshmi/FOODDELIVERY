from rest_framework import serializers
from .models import Delivery_Partners, DeliveryPerson
from restaurants.models import Restaurant
from user.serializer import UserSerializer
from orders.serializer import OrderSerializer
from user.models import User

class DeliveryPartnerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Delivery_Partners
        fields = ['partner_id', 'name', 'email', 'phone', 'is_available', 'max_orders', 'user']

    def get_user(self, obj):
        return {
            "id": str(obj.user.id),
        }

    
        
class DeliveryPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryPerson
        fields = [
            'person_id',
            'partner',
            'is_available',
            'assigned_order',
            'vehicle_number',
            'status',
        ]
    
    def create(self, validated_data):
        return DeliveryPerson.objects.create(**validated_data)