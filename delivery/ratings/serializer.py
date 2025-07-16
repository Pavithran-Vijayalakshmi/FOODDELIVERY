from rest_framework import serializers
from .models import rating

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = rating
        fields = '__all__'
        read_only_fields = ['user', 'created_at']
