from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializer import CouponApplySerializer, CouponSerializer
from .models import Coupon, CouponUsage
from orders.models import orders,Cart
from django.utils import timezone
from rest_framework import status

class ApplyCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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

        return Response({
            "message": "Coupon applied successfully",
            "original_total": total,
            "discount_percent": coupon.discount_percent,
            "discounted_total": discounted_total
        })

class CreateCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'admin':
            return Response({"detail": "Only admin users can create coupons."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CouponSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class RemoveCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # Remove the applied_coupon from all their cart items
        Cart.objects.filter(user=user).update(applied_coupon=None)

        return Response({
            "message": "Coupon removed successfully from cart."
        }, status=status.HTTP_200_OK)