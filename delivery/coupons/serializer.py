from rest_framework import serializers
from .models import Coupon, CouponUsage 
from django.utils import timezone

class CouponApplySerializer(serializers.Serializer):
    code = serializers.CharField()

    def validate_code(self, value):
        try:
            coupon =  Coupon.objects.get(code=value, is_active=True)
        except  Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired coupon")
        if coupon.end_time < timezone.now():
            raise serializers.ValidationError("Coupon has expired")
        user = self.context['request'].user
        if  CouponUsage.objects.filter(user=user, coupon=coupon).exists():
            raise serializers.ValidationError("You have already used this coupon")
        return value
    

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount_percent', 'start_time', 'end_time', 'is_active']
        read_only_fields = ['id']
