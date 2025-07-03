from rest_framework import serializers
from .models import restaurantsModel

class restaurantsSerializer(serializers.ModelSerializer):
    class Meta:
        model = restaurantsModel
        fields = '__all__'