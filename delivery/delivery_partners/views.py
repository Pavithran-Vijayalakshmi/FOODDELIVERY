from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Delivery_Partners, DeliveryPerson
from .serializer import DeliveryPartnerSerializer, DeliveryPersonSerializer
from orders.models import orders
from orders.serializer import OrderSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

class DeliveryPartnerListView(APIView):
    permission_classes = [AllowAny]
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
    def post(self, request):
        
        if request.user.user_type != 'deliverypartner':
            return Response({'detail': 'Only delivery partners can update this.'}, status=status.HTTP_403_FORBIDDEN)
        
        partner_id = request.data.get("partner_id")
        order_id = request.data.get("order_id")

        if not partner_id or not order_id:
            return Response({"error": "Missing partner_id or order_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            partner = Delivery_Partners.objects.get(partner_id=partner_id)
        except Delivery_Partners.DoesNotExist:
            return Response({"error": "Delivery Partner not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            order = orders.objects.get(id=order_id)
        except orders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if not order.assigned_person:
            return Response({"error": "No delivery person assigned to this order"}, status=status.HTTP_400_BAD_REQUEST)

        delivery_person = order.assigned_person

        if delivery_person.partner != partner:
            return Response({"error": "This delivery person does not belong to your partner account"}, status=status.HTTP_403_FORBIDDEN)

        delivery_status = delivery_person.status

        # Map delivery person status → order status
        status_mapping = {
            'picked_up': 'out_for_delivery',
            'en_route': 'out_for_delivery',
            'delivered': 'delivered',
            'returned': 'cancelled',
        }

        new_order_status = status_mapping.get(delivery_status)

        if not new_order_status:
            return Response({
                "error": f"Cannot update order from delivery status: '{delivery_status}'"
            }, status=status.HTTP_400_BAD_REQUEST)

        if order.status == new_order_status:
            return Response({"message": "Order is already in that status"}, status=status.HTTP_200_OK)

        order.status = new_order_status
        order.save()

        return Response({
            "message": f"Order status updated to '{new_order_status}'"
        }, status=status.HTTP_200_OK)
    
    
    
    
class DeliveryPersonCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'deliveryperson':
            return Response({'detail': 'Only delivery persons can create this.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = DeliveryPersonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateDeliveryPersonStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'deliveryperson':
            return Response({'detail': 'Only delivery persons can create this.'}, status=status.HTTP_403_FORBIDDEN)
        
        person_id = request.data.get("person_id")
        new_status = request.data.get("status")

        if not person_id or not new_status:
            return Response({"error": "Missing person_id or status"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            person = DeliveryPerson.objects.get(person_id=person_id)
        except DeliveryPerson.DoesNotExist:
            return Response({"error": "DeliveryPerson not found"}, status=status.HTTP_404_NOT_FOUND)

        current_status = person.status

        VALID_TRANSITIONS = {
            'idle': ['picked_up'],
            'picked_up': ['en_route', 'returned'],
            'en_route': ['delivered', 'returned'],
            'delivered': [],
            'returned': [],
        }

        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            return Response({
                "error": f"Invalid transition from '{current_status}' to '{new_status}'"
            }, status=status.HTTP_400_BAD_REQUEST)

        person.status = new_status
        person.save()

        return Response({
            "message": f"Delivery person status updated to '{new_status}'"
        }, status=status.HTTP_200_OK)
        
        
class DeliveryPersonListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type != 'deliverypartner':
            return Response({'detail': 'Only delivery partners can access this.'}, status=status.HTTP_403_FORBIDDEN)

        partner_id = request.query_params.get('partner_id')
        
        if not partner_id:
            return Response({'error': 'Missing partner_id in query parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            partner = Delivery_Partners.objects.get(partner_id=partner_id)
        except Delivery_Partners.DoesNotExist:
            return Response({'error': 'Delivery partner not found.'}, status=status.HTTP_404_NOT_FOUND)

        # # Ensure the requesting user can only see their own delivery persons
        # if partner.user != request.user:
        #     return Response({'error': 'You are not authorized to view delivery persons for this partner.'}, status=status.HTTP_403_FORBIDDEN)

        delivery_persons = DeliveryPerson.objects.filter(partner=partner)

        serializer = DeliveryPersonSerializer(delivery_persons, many=True)
        return Response(serializer.data)
      

        
class AssignOrderToDeliveryPersonView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'deliverypartner':
            return Response({'detail': 'Only delivery partners can assign an order.'}, status=status.HTTP_403_FORBIDDEN)
        
        order_id = request.data.get('order_id')
        person_id = request.data.get('person_id')

        # try:
        #     delivery_partner_profile = Delivery_Partners.objects.get(user=request.user)
        # except Delivery_Partners.DoesNotExist:
        #     return Response({'detail': 'Associated delivery partner not found.'}, status=status.HTTP_400_BAD_REQUEST)
        
        

        try:
            delivery_person = DeliveryPerson.objects.get(person_id=person_id)
        except DeliveryPerson.DoesNotExist:
            return Response({"error": "Delivery person not found or not under this partner."}, status=status.HTTP_404_NOT_FOUND)

        if not delivery_person.is_available:
            return Response({"error": "Delivery person is not available."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = orders.objects.get(id=order_id)
        except orders.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        # Assign the order
        delivery_person.assigned_order = order
        delivery_person.is_available = False
        delivery_person.save()

        order.status = "out_for_delivery"
        order.save()

        return Response({"message": "Order assigned successfully."}, status=status.HTTP_200_OK)