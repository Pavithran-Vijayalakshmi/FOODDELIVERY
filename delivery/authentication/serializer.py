from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authentication import authenticate
from restaurants.models import Restaurant
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

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




class LoginSerializer(serializers.Serializer):
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Invalid username or password")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        data['user'] = user
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],  
        style={'input_type': 'password'},
        help_text=_("Password must meet Django's password validation rules.")
    )
    class Meta:
        model = User    
        fields = ["username", "password", "name", "email", "phone", "user_type"]

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            phone = validated_data['phone'],
            user_type= validated_data['user_type'],
            name = validated_data['name'], 
            
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    

