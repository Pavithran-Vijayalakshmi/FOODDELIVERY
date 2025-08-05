from decimal import Decimal
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializer import CouponApplySerializer, CouponSerializer
from .models import Coupon, CouponUsage
from orders.models import Orders,Cart
from django.utils import timezone
from rest_framework import status
from common.response import api_response

class ApplyCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message= "Only customers can use coupons.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = CouponApplySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        user = request.user
        coupon = Coupon.objects.get(code=code)

        cart_items = Cart.objects.filter(user=user)
        total = sum([item.menu_item.price * item.quantity for item in cart_items])
        discount_rate = Decimal(coupon.discount_percent) / Decimal(100)
        discount_amount = discount_rate * total
        discounted_total = total - discount_amount

        # Store usage
        Cart.objects.filter(user=user).update(applied_coupon=coupon)

        return api_response(
            message= "Coupon applied successfully",
            data = {
            "original_total": total,
            "discount_percent": coupon.discount_percent,
            "discounted_total": discounted_total
        },status_code=status.HTTP_200_OK)

class CreateCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return api_response(message = "Only admin users can create coupons.", status_code=status.HTTP_403_FORBIDDEN)

        serializer = CouponSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(data = serializer.data,  status_code=status.HTTP_201_CREATED)
        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Delete a coupon (admin only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return api_response(
                message="Only admin users can delete coupons.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        coupon_id = request.query_params.get('id')
        if not coupon_id:
            return api_response(
                message="Coupon ID is required in query parameters (?id=)",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        coupon = get_object_or_404(Coupon, id=coupon_id)
        
        # Optional: Check if coupon is being used in any active orders
        if coupon.orders.filter(status__in=['pending', 'processing']).exists():
            return api_response(
                message="Cannot delete coupon with active orders",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        coupon.delete()
        return api_response(
            message="Coupon deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
class RemoveCouponView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message= "Only customers can use coupons.", status_code=status.HTTP_403_FORBIDDEN)
        
        # Remove the applied_coupon from all their cart items
        Cart.objects.filter(user=user).update(applied_coupon=None)

        return api_response(
            message= "Coupon removed successfully from cart."
        , status_code=status.HTTP_200_OK)