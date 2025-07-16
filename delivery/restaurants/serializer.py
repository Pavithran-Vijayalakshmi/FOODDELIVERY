from rest_framework import serializers
from ratings.models import rating
from .models import restaurants, MenuItem
from django.db.models import Avg

class RestaurantListSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    class Meta:
        model = restaurants
        fields = ['id', 'name', 'description', 'average_rating']  

    def get_average_rating(self, obj):
        # if rating.objects.filter(restaurant=obj) is not None:
            avg_rating = rating.objects.filter(restaurant=obj).aggregate(avg=Avg('rating'))['avg']
            if avg_rating is not None:
                return round(avg_rating, 2)
            return None

class RestaurantDetailSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    menu_items = serializers.SerializerMethodField()

    class Meta:
        model = restaurants
        fields = ['id', 'name', 'description', 'city','address', 'phone', 'email',
                  'opening_time', 'closing_time', 'is_open', 'created_at',
                  'average_rating', 'total_ratings', 'menu_items']

    def get_average_rating(self, obj):
        if rating.objects.filter(restaurant=obj) is not None:
            avg_rating = rating.objects.filter(restaurant=obj).aggregate(avg=Avg('rating'))['avg']
            if avg_rating is not None:
                return round(avg_rating, 2)
            return None

    def get_total_ratings(self, obj):
        return rating.objects.filter(restaurant=obj).count()
    
    def get_menu_items(self, obj):
        items = MenuItem.objects.filter(restaurant=obj)
        return MenuItemSerializer(items, many=True).data
    
    
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
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category', 'image_url',
                   'restaurant','is_available', 'created_at',
                  'average_rating', 'total_ratings']

    def get_average_rating(self, obj):
        if rating.objects.filter(menu_item=obj) is not None:
            avg_rating = rating.objects.filter(menu_item=obj).aggregate(avg=Avg('rating'))['avg']
            if avg_rating is not None:
                return round(avg_rating, 2)
            return None


    def get_total_ratings(self, obj):
        return rating.objects.filter(menu_item=obj).count()
    
class MenuItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'category']
        
        
class MenuItemCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category', 'image_url',
                'is_available']