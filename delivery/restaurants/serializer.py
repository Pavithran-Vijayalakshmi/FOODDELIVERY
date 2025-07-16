from rest_framework import serializers
from .models import restaurants, MenuItem

class RestaurantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = restaurants
        fields = [
            'id', 'name','city',
        ]

class RestaurantDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = restaurants
        fields = [
            'id', 'name','city', 'description', 'phone', 'email',
            'address', 'opening_time', 'closing_time', 'is_open', 'created_at',
        ]

class RestaurantCreateSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(write_only = True)
    class Meta:
        model = restaurants
        fields = [
            'name','city','description','phone','email','address','opening_time','closing_time','is_open',
        ]

    def create(self, validated_data):
        return restaurants.objects.create(**validated_data)
    

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'
        read_only_fields = ['restaurant']
    
class MenuItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'category']