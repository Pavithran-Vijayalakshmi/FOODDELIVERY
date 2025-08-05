from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authentication import authenticate
from restaurants.models import Restaurant
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
import phonenumbers
from common.base import Region
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from delivery.backend import EmailOrPhoneBackend


User = get_user_model()

from orders.models import Orders
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user_type'] = self.user.user_type
        return data




# class LoginSerializer(serializers.Serializer):
    
#     email = serializers.CharField(required=True)
#     password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

#     def validate(self, data):
#         user = authenticate(email=data['email'], password=data['password'])
#         if user is None:
#             raise serializers.ValidationError("Invalid email or password")
#         if not user.is_active:
#             raise serializers.ValidationError("User account is disabled")
#         data['user'] = user
#         return data



class LoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )

    def validate(self, data):
        email_or_phone = data.get('email_or_phone')
        password = data.get('password')
        
        # Convert to string if numeric phone is provided
        if isinstance(email_or_phone, (int, float)):
            email_or_phone = str(int(email_or_phone))
        
        # Determine if input is email or phone
        try:
            validate_email(email_or_phone)
            auth_kwargs = {'email': email_or_phone}
        except ValidationError:
            if not email_or_phone.isdigit():
                raise serializers.ValidationError({
                    "non_field_errors": ["Please enter a valid email or phone number"]
                })
            auth_kwargs = {'phone_number': email_or_phone}
        
        # Authenticate using custom backend
        user = authenticate(
            request=self.context.get('request'),
            **auth_kwargs,
            password=password
        )
        
        if user is None:
            raise serializers.ValidationError({
                "non_field_errors": ["Invalid credentials"]
            })
            
        if not user.is_active:
            raise serializers.ValidationError({
                "non_field_errors": ["User account is disabled"]
            })
            
        data['user'] = user
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text=_("Password must meet Django's password validation rules.")
    )
    
    phone_region = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        write_only=True,
        help_text="ID of the phone region"
    )
    
    phone_number = serializers.CharField(
        write_only=True,
        help_text="Phone number without country code (e.g., '5551234567')"
    )

    class Meta:
        model = User
        fields = ['email',  'password', 'phone_region', 'phone_number']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        region = data.get('phone_region')
        phone_number = data.get('phone_number')
        
        if region and phone_number:
            try:
                # Format: +<calling_code><phone_number> (e.g., +15551234567)
                full_number = f"+{region.calling_code}{phone_number}"
                parsed = phonenumbers.parse(full_number, region.code)
                
                if not phonenumbers.is_valid_number(parsed):
                    raise serializers.ValidationError({
                        'phone_number': 'Invalid phone number for the selected region'
                    })
                
                # Store formatted number in E.164 format
                data['formatted_phone'] = phonenumbers.format_number(
                    parsed, 
                    phonenumbers.PhoneNumberFormat.E164
                )
                
            except phonenumbers.NumberParseException:
                raise serializers.ValidationError({
                    'phone_number': 'Invalid phone number format'
                })
        return data

    def create(self, validated_data):
        region = validated_data.pop('phone_region')
        phone_number = validated_data.pop('phone_number')
        formatted_phone = validated_data.pop('formatted_phone')
        
        user_type = self.context.get('user_type', 'customer')
        
        user = User.objects.create(
            email=validated_data['email'],
            user_type=user_type,
            phone_region=region,
            phone_number=phone_number  # Store the formatted number
        )
        
        user.set_password(validated_data['password'])
        user.save()
        return user    

