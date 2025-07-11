from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authentication import authenticate

User = get_user_model()

from orders.models import orders
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
    password = serializers.CharField(write_only = True)
    class Meta:
        model = User    
        fields = ["username", "password", "name", "email", "phone", "user_type"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    

