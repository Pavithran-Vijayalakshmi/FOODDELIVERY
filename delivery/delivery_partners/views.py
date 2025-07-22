from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Delivery_Partners
from .serializer import DeliveryPartnerSerializer
from orders.models import orders
from orders.serializer import OrderSerializer
from rest_framework.permissions import IsAuthenticated

class DeliveryPartnerListView(APIView):
    def get(self, request):
        name = request.query_params.get('name')
        if name:
            partners = Delivery_Partners.objects.filter(name__icontains=name)
        else:
            partners = Delivery_Partners.objects.all()
        serializer = DeliveryPartnerSerializer(partners, many=True)
        return Response(serializer.data)

class DeliveryPartnerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'deliverypartner':
            return Response({'detail': 'Only delivery partners can create this.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = DeliveryPartnerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeliveryPartnerRetrieveView(APIView):
    def get(self, request):
        partner_id = request.query_params.get('id')
        if not partner_id:
            return Response({"error": "Missing 'id' in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            partner = Delivery_Partners.objects.get(pk=partner_id)
        except Delivery_Partners.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = DeliveryPartnerSerializer(partner)
        return Response(serializer.data)

class DeliveryPartnerUpdateView(APIView):
    def patch(self, request):
        partner_id = request.query_params.get('id')
        if not partner_id:
            return Response({"error": "Missing 'id' in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            partner = Delivery_Partners.objects.get(pk=partner_id)
        except Delivery_Partners.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = DeliveryPartnerSerializer(partner, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeliveryPartnerDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        partner_id = request.query_params.get('id')
        if not partner_id:
            return Response({"error": "Missing 'id' in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            partner = Delivery_Partners.objects.get(pk=partner_id)
        except Delivery_Partners.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        partner.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class UpdateOrderStatusByPartnerView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request):
        order_id = request.query_params.get('order_id')
        new_status = request.query_params.get('status')
        partner_id = request.query_params.get('partner_id')

        if not order_id or not new_status:
            return Response({"error": "Missing 'order_id' or 'status' in query parameters"}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = ['out_for_delivery', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return Response({"error": f"Invalid status. Allowed: {valid_statuses}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = orders.objects.get(pk=order_id)
        except orders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        # order.status = new_status
        order.status = new_status
        order.save()

        if partner_id:
            try:
                partner = Delivery_Partners.objects.get(pk=partner_id)
                partner.is_available = False if new_status == 'out_for_delivery' else True
                partner.save()
            except Delivery_Partners.DoesNotExist:
                return Response({"error": "Delivery partner not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"message": f"Order status updated to '{new_status}'"}, status=status.HTTP_200_OK)