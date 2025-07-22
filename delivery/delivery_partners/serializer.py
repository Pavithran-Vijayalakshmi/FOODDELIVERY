from rest_framework import serializers
from .models import Delivery_Partners, DeliveryPerson
from restaurants.models import restaurants
from user.serializer import UserSerializer
from orders.serializer import OrderSerializer

class DeliveryPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery_Partners
        fields = ['partner_id','name','email','phone', 'is_available','max_orders']
        
        def create(self, validated_data):
            partner = Delivery_Partners.objects.create(**validated_data)
            partner.assigned_restaurants.set(restaurants.objects.all())
            return partner

        
        
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