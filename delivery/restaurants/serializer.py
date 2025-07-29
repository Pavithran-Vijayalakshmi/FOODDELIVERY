from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from ratings.models import Rating
from .models import Restaurant, MenuItem, Offer, Category
from django.db.models import Avg

class RestaurantListSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'description', 'average_rating']  

    def get_average_rating(self, obj):
        # if rating.objects.filter(restaurant=obj) is not None:
            avg_rating = Rating.objects.filter(restaurant=obj).aggregate(avg=Avg('rating'))['avg']
            if avg_rating is not None:
                return round(avg_rating, 2)
            return None

class RestaurantDetailSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    menu_items = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'description', 'city', 'restaurant_primary_phone', 'email',
                  'opening_time', 'closing_time', 'is_open', 'created_at',
                  'average_rating', 'total_ratings', 'menu_items', 'offers']

    def get_average_rating(self, obj):
        if Rating.objects.filter(restaurant=obj) is not None:
            avg_rating = Rating.objects.filter(restaurant=obj).aggregate(avg=Avg('rating'))['avg']
            if avg_rating is not None:
                return round(avg_rating, 2)
            return None

    def get_total_ratings(self, obj):
        return Rating.objects.filter(restaurant=obj).count()
    
    def get_menu_items(self, obj):
        items = MenuItem.objects.filter(restaurant=obj)
        return MenuItemSerializer(items, many=True).data
    
    def get_offers(self, obj):
        current_time = timezone.now()
        offers = Offer.objects.filter(restaurant=obj, start_date__lte=current_time, end_date__gte=current_time)
        return OfferSerializer(offers, many=True).data
    
    
class RestaurantCreateSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(write_only = True)
    class Meta:
        model = Restaurant
        fields = ['id',
            'name','city','description','restaurant_primary_phone','email','opening_time','closing_time','is_open',
        ]

    def create(self, validated_data):
        return Restaurant.objects.create(**validated_data)
    

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active']
        

class MenuItemSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()
    # category = CategorySerializer(read_only=True)
    
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price',
                   'restaurant','is_available', 'created_at',
                  'average_rating','review', 'total_ratings','discounted_price']
        
    def get_review(self, obj):
        return [
        {
            'author': rating.user.name,
            'review': rating.review
        }
        for rating in Rating.objects.select_related('user').filter(menu_item=obj)
    ]


    def get_average_rating(self, obj):
        if Rating.objects.filter(menu_item=obj) is not None:
            avg_rating = Rating.objects.filter(menu_item=obj).aggregate(avg=Avg('rating'))['avg']
            if avg_rating is not None:
                return round(avg_rating, 2)
            return None

    def get_total_ratings(self, obj):
        return Rating.objects.filter(menu_item=obj).count()
    
    def get_applicable_offers(self, obj):
        now = timezone.now()

        item_offers = Offer.objects.filter(
            menu_item=obj,
            restaurant=obj.restaurant,
            is_active= True,
            start_date__lte=now,
            end_date__gte=now,
            minimum_order_amount__lte=obj.price
        )

        restaurant_offers = Offer.objects.filter(
            menu_item__isnull=True,
            restaurant=obj.restaurant,
            is_active = True,
            start_date__lte=now,
            end_date__gte=now,
            minimum_order_amount__lte=obj.price
        )

        return list(item_offers) + list(restaurant_offers)

    def get_offers(self, obj):
        offers = self.get_applicable_offers(obj)
        return OfferSerializer(offers, many=True).data

    def get_discounted_price(self, obj):
        offers = self.get_applicable_offers(obj)
        if not offers:
            return None  # Or return obj.price if you always want to show a price

        best_offer = max(offers, key=lambda o: o.percentage)
        discount = (best_offer.percentage / 100) * obj.price
        return round(obj.price - discount, 2)    


class MenuItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'category']
        
        
class MenuItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category','item_type',
                'is_available']
        
        
class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'
    
    
    
    def create(self, validated_data):
        return Offer.objects.create(**validated_data)
    
    
        
    
