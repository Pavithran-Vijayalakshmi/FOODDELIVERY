import phonenumbers
from rest_framework import serializers

from orders.models.notification import Notification
from .models import User, Favorite, SavedAddress
from orders.models.models import Cart, Orders
from orders.serializer import OrderSerializer, CartSerializer, UserNotificationSerializer
from restaurants.models import Restaurant, MenuItem, Offer, Category
from restaurants.serializer import  RestaurantDetailSerializer, MenuItemSerializer, OfferSerializer, RestaurantCreateSerializer
from decimal import Decimal
from common.models import City, Country,State
from ratings.models import Rating
from django.utils import timezone
from django.db.models import Avg


def get_cart(self, obj):
        cart_items = Cart.objects.filter(user=obj).select_related('menu_item__restaurant')
        grouped = {}

        for item in cart_items:
            restaurant = item.menu_item.restaurant
            rest_id = restaurant.id

            if rest_id not in grouped:
                grouped[rest_id] = {
                    "restaurant_id": rest_id,
                    "restaurant_name": restaurant.name,
                    "items": [],
                    "total": Decimal("0.00")
                }

            item_data = CartSerializer(item, context=self.context).data
            grouped[rest_id]["items"].append(item_data)

            discounted_total = Decimal(item_data.get("discounted_total", "0.00"))
            grouped[rest_id]["total"] += discounted_total

        for group in grouped.values():
            group["total"] = round(group["total"], 2)

        return list(grouped.values())

def get_favorites(self, obj):
    favorites_qs = Favorite.objects.filter(user=obj)
    return FavoriteSerializer(favorites_qs, many=True).data
        
def get_saved_addresses(self, obj):
    saved_addresses = SavedAddress.objects.filter(user=obj)
    return SavedAddressSerializer(saved_addresses, many=True).data

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'phone_region','phone_number', 'user_type', 'is_admin',
            'admin_access_level', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    

class AdminUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email', 'name', 'phone_region','phone_number', 'password', 'user_type',
            'is_admin', 'admin_access_level'
        ]
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            phone=validated_data['phone'],
            user_type=validated_data.get('user_type', 'admin'),
            is_admin=validated_data.get('is_admin', False),
            admin_access_level=validated_data.get('admin_access_level')
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)
    cart = serializers.SerializerMethodField()
    favorites = serializers.SerializerMethodField()
    saved_addresses = serializers.SerializerMethodField()
    notifications = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_region', 'phone_number', 'user_type', 'created_at',
            'orders', 'cart', 'favorites', 'saved_addresses', 'notifications'
        ]

    def get_cart(self, obj):
        return get_cart(self, obj)

    def get_favorites(self, obj):
        return get_favorites(self, obj)

    def get_saved_addresses(self, obj):
        return get_saved_addresses(self, obj)
    
    def get_notifications(self, obj):
        notifications = Notification.objects.filter(user=obj)
        return UserNotificationSerializer(notifications, many=True).data

class UserCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_region','phone_number', 'user_type'
        ]
        
    


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    dob = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False)
    
    # Read-only fields for display
    country_name = serializers.CharField(source='country.name', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    # Address fields that can be updated
    address_line1 = serializers.CharField(required=False)
    address_line2 = serializers.CharField(required=False, allow_blank=True)
    city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), 
        required=False,
        help_text="ID of the city"
    )
    state = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), 
        required=False,
        help_text="ID of the state"
    )
    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), 
        required=False,
        help_text="ID of the country"
    )
    pincode = serializers.CharField(required=False)
    label = serializers.CharField(
        required=False,
        help_text="Label for the address (e.g., Home, Work)"
    )

    class Meta:
        model = User
        fields = [
            'name', 'email', 'phone_region', 'phone_number', 'dob', 'gender', 'profile_picture',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'pincode', 'label',
            'country_name', 'state_name', 'city_name',
            'account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'upi_id'
        ]
        extra_kwargs = {
            'email': {'read_only': True},  # Email shouldn't be changed
            'phone_number': {'required': False},
            'profile_picture': {'required': False}
        }

    def validate(self, data):
        # Validate phone number format if provided
        phone_number = data.get('phone_number')
        if phone_number:
            region = data.get('phone_region', self.instance.phone_region if self.instance else None)
            if not region:
                raise serializers.ValidationError(
                    {"phone_number": "Phone region is required when updating phone number"}
                )
            
            try:
                parsed = phonenumbers.parse(phone_number, region.code)
                if not phonenumbers.is_valid_number(parsed):
                    raise serializers.ValidationError(
                        {"phone_number": "Invalid phone number for the selected region"}
                    )
            except phonenumbers.NumberParseException:
                raise serializers.ValidationError(
                    {"phone_number": "Invalid phone number format"}
                )

        # Validate address completeness if any address fields are provided
        address_fields = ['address_line1', 'city', 'state', 'country', 'pincode']
        if any(field in data for field in address_fields):
            missing_fields = [field for field in address_fields if field not in data]
            if missing_fields:
                raise serializers.ValidationError(
                    {field: "This field is required when updating address" for field in missing_fields}
                )

        return data

    def update(self, instance, validated_data):
        # Handle profile picture separately
        profile_picture = validated_data.pop('profile_picture', None)
        if profile_picture is not None:
            instance.profile_picture = profile_picture

        # Handle address data
        label = validated_data.pop('label', None)
        address_data = {
            'address_line1': validated_data.pop('address_line1', None),
            'address_line2': validated_data.pop('address_line2', None),
            'city': validated_data.pop('city', None),
            'state': validated_data.pop('state', None),
            'country': validated_data.pop('country', None),
            'pincode': validated_data.pop('pincode', None),
        }

        # Update basic profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Save address if all required fields are present
        if all(address_data.values()) and label:
            SavedAddress.objects.update_or_create(
                user=instance,
                label=label,
                defaults=address_data
            )

        return instance
    
class FavoriteSerializer(serializers.ModelSerializer):
    restaurant = RestaurantDetailSerializer(read_only=True)
    menu_item = MenuItemSerializer(read_only=True)
    class Meta:
        model = Favorite
        fields = ['id', 'restaurant', 'menu_item', 'created_at']
        read_only_fields = ['id', 'created_at']
        
        
class SavedAddressSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    class Meta:
        model = SavedAddress
        fields = [
            'id', 'label', 'address_line1', 'address_line2',
            'city', 'state', 'country', 'is_default',
            'city_name', 'state_name', 'country_name',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'address_line1': {'required': True},
            'label': {'required': True}
        }
    
    def validate(self, data):
        """Validate the entire address including duplicate check"""
        user = self.context['request'].user
        address_line1 = data.get('address_line1')
        city = data.get('city')
        
        # Check for duplicate address (same address_line1 + city)
        if SavedAddress.objects.filter(
            user=user,
            address_line1=address_line1,
            city=city
        ).exists():
            raise serializers.ValidationError(
                {'address': 'You already have this address saved.'}
            )
        
        return data
    
    def create(self, validated_data):
        """Create new address after all validations pass"""
        # Handle default address logic
        if validated_data.get('is_default', False):
            SavedAddress.objects.filter(
                user=self.context['request'].user,
                is_default=True
            ).update(is_default=False)
        
        return SavedAddress.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        
        
class RestaurantDetailSerializer(serializers.ModelSerializer):
    country_name = serializers.SerializerMethodField()
    state_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    menu_items = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'description', 'country_name', 'state_name', 'city_name',
                  'restaurant_primary_phone', 'email',
                  'opening_time', 'closing_time', 'is_open',
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
    
    def get_country_name(self, obj):
        return obj.city.state.country.name if obj.city and obj.city.state else None

    def get_state_name(self, obj):
        return obj.city.state.name if obj.city and obj.city.state else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None
    