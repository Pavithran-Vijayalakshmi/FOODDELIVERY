from datetime import timedelta
from django.utils import timezone
import phonenumbers
from rest_framework import serializers
from ratings.models import Rating
from .models import Restaurant, MenuItem, Offer, Category
from django.db.models import Avg
from common.models import Country,City, State, Region
from django.core.exceptions import ValidationError
import datetime

class TimeAMPMField(serializers.Field):
    """Custom field to handle AM/PM time input"""
    
    def to_representation(self, value):
        # Convert 24-hour time to 12-hour AM/PM format when displaying
        if value:
            return value.strftime('%I:%M %p')
        return None
    
    def to_internal_value(self, data):
        # Convert 12-hour AM/PM input to 24-hour time
        try:
            time_obj = datetime.datetime.strptime(data, '%I:%M %p').time()
            return time_obj
        except ValueError:
            raise ValidationError("Invalid time format. Please use 'HH:MM AM/PM' format (e.g., '09:30 AM' or '05:45 PM')")



class RestaurantListSerializer(serializers.ModelSerializer):
    country_name = serializers.SerializerMethodField()
    state_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    

    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'description', 
            'average_rating', 'country_name', 
            'state_name', 'city_name', 'is_approved'
        ]

    def get_country_name(self, obj):
        return obj.city.state.country.name if obj.city and obj.city.state else None

    def get_state_name(self, obj):
        return obj.city.state.name if obj.city and obj.city.state else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None
    
    def get_average_rating(self, obj):
        # if rating.objects.filter(restaurant=obj) is not None:
            avg_rating = Rating.objects.filter(restaurant=obj).aggregate(avg=Avg('rating'))['avg']
            if avg_rating is not None:
                return round(avg_rating, 2)
            return None

class RestaurantDetailSerializer(serializers.ModelSerializer):
    country_name = serializers.SerializerMethodField()
    state_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    menu_items = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    opening_time = TimeAMPMField()
    closing_time = TimeAMPMField()

    class Meta:
        model = Restaurant
        fields = fields = [
            'id', 'name', 'description', 'email', 'region','business_phone','opening_time', 'closing_time', 
            'is_open', 'restaurant_type', 'address_line1', 'address_line2', 
            'pincode', 'latitude', 'longitude','menu_items',
            'pan_card', 'gst_number', 'fssai_license', 'menu_image', 'profile_image',
            'payout_frequency', 'payment_method_preference', 'commission_percentage',
            'account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'upi_id',
            'country_name', 'state_name', 'city_name', 'average_rating','total_ratings','offers', 'is_approved'
        ]

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
    
    def get_country_name(self, obj):
        return obj.city.state.country.name if obj.city and obj.city.state else None

    def get_state_name(self, obj):
        return obj.city.state.name if obj.city and obj.city.state else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None
    

class RestaurantCreateSerializer(serializers.ModelSerializer):
    opening_time = TimeAMPMField()
    closing_time = TimeAMPMField()
    business_phone = serializers.CharField(required=True)
    region = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        required=True
    )
    country_name = serializers.CharField(source='country.name', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), 
        required=False,
        allow_null=True,
        help_text="ID of the city"
    )
    state = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), 
        required=False,
        allow_null=True,
        help_text="ID of the state"
    )
    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), 
        required=False,
        allow_null=True,
        help_text="ID of the country"
    )

    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'description', 'email', 'opening_time', 'closing_time', 
            'is_open', 'restaurant_type', 'address_line1', 'address_line2', 
            'pincode', 'latitude', 'longitude', 'business_phone', 'region',
            'pan_card', 'gst_number', 'fssai_license', 'menu_image', 'profile_image',
            'account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'upi_id',
            'country_name', 'state_name', 'city_name', 'is_approved', 'city','state','country'#
        ]
        read_only_fields = ['is_approved', 'country_name', 'state_name', 'city_name']

    def validate(self, data):
        region = data.get('region')
        phone_number = data.get('business_phone')
        
        if not region or not phone_number:
            raise serializers.ValidationError({
                'business_phone': 'Both region and phone number are required'
            })

        try:
            full_number = f"+{region.calling_code}{phone_number}"
            parsed = phonenumbers.parse(full_number, region.code)
            
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError({
                    'business_phone': 'Invalid phone number for the selected region'
                })
            
            data['formatted_phone'] = phonenumbers.format_number(
                parsed, 
                phonenumbers.PhoneNumberFormat.E164
            )
            
        except phonenumbers.NumberParseException as e:
            raise serializers.ValidationError({
                'business_phone': f'Invalid phone number format: {str(e)}'
            })
        if data['opening_time'] >= data['closing_time']:
            raise serializers.ValidationError({
                'closing_time': 'Closing time must be after opening time'
            })
            
        opening = data['opening_time']
        closing = data['closing_time']
        
        # Convert times to datetime for calculation
        opening_dt = datetime.datetime.combine(datetime.date.today(), opening)
        closing_dt = datetime.datetime.combine(datetime.date.today(), closing)
        
        # Handle cases where closing is the next day (e.g., 22:00 to 06:00)
        if closing_dt < opening_dt:
            closing_dt += datetime.timedelta(days=1)
        
        time_diff = closing_dt - opening_dt
        
        if time_diff < datetime.timedelta(hours=10):
            raise serializers.ValidationError({
                'closing_time': 'Restaurant must be open for at least 12 hours.'
            })

        city = data.get('city')
        if city:
            # Fetch state from the selected city
            state = city.state
            data['state'] = state
            
            # Fetch country from the state
            country = state.country
            data['country'] = country

        return data

    def create(self, validated_data):
        region = validated_data.pop('region')
        phone_number = validated_data.pop('business_phone')
        formatted_phone = validated_data.pop('formatted_phone', None)
        
        restaurant = Restaurant.objects.create(
            **validated_data,
            owner=self.context['request'].user,
            created_by = self.context['request'].user,
            region=region,
            business_phone=phone_number,
            is_approved=False
        )
        return restaurant

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active']
        
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return Offer.objects.create(**validated_data)

class MenuItemSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price',
                'restaurant','is_available', 'created_at','image',
                'average_rating','review', 'total_ratings','discounted_price', 'is_approved']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return Offer.objects.create(**validated_data)
        
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
    # image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price', 'category','item_type', 'restaurant',
                'is_available', 'image']
        
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
        
        
class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'
    
    
    
    def create(self, validated_data):
        return Offer.objects.create(**validated_data)
    
    
        
    
# In serializer.py
class RestaurantUpdateSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'description', 'email', 'opening_time', 'closing_time', 
            'is_open', 'restaurant_type', 'address_line1', 'address_line2', 'city', 
            'state', 'country', 'pincode', 'latitude', 'longitude',
            'pan_card', 'gst_number', 'fssai_license', 'menu_image', 'profile_image',
            'payout_frequency', 'payment_method_preference', 'commission_percentage',
            'account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'upi_id',
            'country_name', 'state_name', 'city_name'
        ]
        read_only_fields = ['is_approved']

    def validate(self, data):
        # Check if sensitive fields are being updated
        sensitive_fields = [
            'pan_card', 'gst_number', 'fssai_license',
            'account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'upi_id'
        ]
        
        if any(field in data for field in sensitive_fields):
            # If any sensitive field is being updated, require admin approval again
            data['is_approved'] = False
            
        return data

    def update(self, instance, validated_data):
        # Handle file uploads separately if needed
        menu_image = validated_data.pop('menu_image', None)
        profile_image = validated_data.pop('profile_image', None)
        
        if menu_image:
            instance.menu_image = menu_image
        if profile_image:
            instance.profile_image = profile_image
            
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance