from .base import Region
from rest_framework import serializers

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'code', 'name', 'calling_code']