from rest_framework import serializers
from .models import Delivery_Partners
from restaurants.models import restaurants

class DeliveryPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery_Partners
        fields = ['name','email','phone','vehicle_number', 'is_available','max_orders']
        
        def create(self, validated_data):
            partner = Delivery_Partners.objects.create(**validated_data)
            partner.assigned_restaurants.set(restaurants.objects.all())
            return partner

        
        
