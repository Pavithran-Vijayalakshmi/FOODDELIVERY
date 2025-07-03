from rest_framework import serializers
from .models import userClass

class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = userClass
        fields = '__all__'
    