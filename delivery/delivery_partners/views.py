from uuid import UUID
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Delivery_Partners, DeliveryPerson
from .serializer import DeliveryPartnerSerializer, DeliveryPersonSerializer
from orders.models import Orders
from orders.serializer import OrderSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from common.types import VALID_TRANSITIONS
from user.models import User
from django.db.models import Max, Q
from restaurants.models import Restaurant



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
        user = request.user

        if user.user_type != 'delivery_partner':
            return Response({"detail": "Only delivery partners can create a profile."}, status=status.HTTP_403_FORBIDDEN)

        # Check if profile already exists
        if hasattr(user, 'delivery_partner_profile'):
            return Response({"detail": "Profile already exists."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        delivery_partner = Delivery_Partners.objects.create(
            user=user,
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            max_orders=data.get('max_orders', 1),
        )
        
        restaurant_ids = data.get('restaurant_id')  # can be a single UUID or list

        if restaurant_ids:
            if isinstance(restaurant_ids, str):  # convert single UUID to list
                restaurant_ids = [restaurant_ids]

            restaurants = Restaurant.objects.filter(id__in=restaurant_ids)
            delivery_partner.assigned_restaurants.set(restaurants)

        return Response({
            "message": "Delivery partner profile created.",
            "partner_id": delivery_partner.partner_id
        }, status=status.HTTP_201_CREATED)

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
        user = request.user
        
        if request.user.user_type != 'delivery_partner':
            return Response({'detail': 'Only delivery partners can update this.'}, status=status.HTTP_403_FORBIDDEN)
        
        order_id = request.data.get("order_id")

        if not order_id:
            return Response({"error": "Missing order_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            partner = Delivery_Partners.objects.get(user=user)
        except Delivery_Partners.DoesNotExist:
            return Response({"error": "Delivery Partner not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if not order.assigned_person:
            return Response({"error": "No delivery person assigned to this order"}, status=status.HTTP_400_BAD_REQUEST)

        delivery_person = order.assigned_person

        if delivery_person.partner != partner:
            return Response({"error": "This delivery person does not belong to your partner account"}, status=status.HTTP_403_FORBIDDEN)

        delivery_status = delivery_person.status

        status_mapping = {
            'picked_up': 'out_for_delivery',
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
        user = request.user

        if user.user_type != 'delivery_person':
            return Response({"detail": "Only delivery persons can create a profile."},
                            status=status.HTTP_403_FORBIDDEN)

        if hasattr(user, 'delivery_person_profile'):
            return Response({"detail": "Profile already exists."},
                            status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        partner_id = data.get('partner')
        try:
            partner_instance = Delivery_Partners.objects.get(partner_id=partner_id)
        except Delivery_Partners.DoesNotExist:
            return Response({"detail": "Invalid partner ID."}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery_person = DeliveryPerson.objects.create(
            user=user,
            
            person_id=data.get('person_id'),
            partner=partner_instance,
            is_available=data.get('is_available'),
            vehicle_number=data.get('vehicle_number'),
        )
        return Response({
                "message": "Delivery person profile created.",
                "person_id": delivery_person.person_id
            }, status=status.HTTP_201_CREATED)


class UpdateDeliveryPersonStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        user = request.user
        if request.user.user_type != 'delivery_person':
            return Response({'detail': 'Only delivery persons can create this.'}, status=status.HTTP_403_FORBIDDEN)
        
        
        new_status = request.data.get("status")

        if not new_status:
            return Response({"error": "Missing status"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            person = DeliveryPerson.objects.get(user = user)
        except DeliveryPerson.DoesNotExist:
            return Response({"error": "DeliveryPerson not found"}, status=status.HTTP_404_NOT_FOUND)

        current_status = person.status

        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            return Response({
                "error": f"Invalid transition from '{current_status}' to '{new_status}'"
            }, status=status.HTTP_400_BAD_REQUEST)

        person.status = new_status
        if new_status == 'idle':
            person.is_available = True
        person.save()

        return Response({
            "message": f"Delivery person status updated to '{new_status}'"
        }, status=status.HTTP_200_OK)
        
        
class DeliveryPersonListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if request.user.user_type != 'delivery_partner':
            return Response({'detail': 'Only delivery partners can access this.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            partner = user.delivery_partner_profile  
        except Delivery_Partners.DoesNotExist:
            return Response({'error': 'Delivery partner profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if partner.user != request.user:
            return Response({'error': 'You are not authorized to view delivery persons for this partner.'}, status=status.HTTP_403_FORBIDDEN)

        delivery_persons = DeliveryPerson.objects.filter(partner=partner)

        serializer = DeliveryPersonSerializer(delivery_persons, many=True)
        return Response(serializer.data)
      

        
class AssignOrderToDeliveryPersonView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Verify user is a delivery partner
        if request.user.user_type != 'delivery_partner':
            return Response(
                {'detail': 'Only delivery partners can assign an order.'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        order_id = request.data.get('order_id')
        person_id = request.data.get('person_id')

        # Get delivery partner profile
        try:
            delivery_partner = request.user.delivery_partner_profile
        except Delivery_Partners.DoesNotExist:
            return Response(
                {'detail': 'Delivery partner profile not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check partner capacity
        if not delivery_partner.has_capacity():
            return Response(
                {"error": f"Maximum order limit ({delivery_partner.max_orders}) reached."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get delivery person (must belong to this partner)
        try:
            delivery_person = DeliveryPerson.objects.get(
                person_id=person_id,
                partner=delivery_partner
            )
        except DeliveryPerson.DoesNotExist:
            return Response(
                {"error": "Delivery person not found or not associated with your partner account."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not delivery_person.is_available:
            return Response(
                {"error": "This delivery person is not currently available."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the order
        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check restaurant assignment (both direct and via order items)
        restaurant = order.restaurant
        order_item_restaurants = set(
            item.menu_item.restaurant_id 
            for item in order.order_items.all()
        )

        # Combine all relevant restaurants
        all_restaurants = {restaurant.id} | order_item_restaurants if restaurant else order_item_restaurants

        # Verify at least one restaurant is assigned to this partner
        partner_restaurants = set(
            delivery_partner.assigned_restaurants.values_list('id', flat=True)
        )

        if not all_restaurants & partner_restaurants:
            return Response(
                {"error": "No restaurants in this order are assigned to your partner account."},
                status=status.HTTP_403_FORBIDDEN
            )

        # For multi-restaurant orders, require specific restaurant selection
        if len(all_restaurants) > 1:
            selected_restaurant_id = request.data.get("restaurant_id")
            if not selected_restaurant_id:
                return Response(
                    {"error": "Multiple restaurants detected. Please specify restaurant_id."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if UUID(selected_restaurant_id) not in partner_restaurants:
                return Response(
                    {"error": "Selected restaurant is not assigned to your partner account."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # All checks passed - assign the order
        delivery_person.assigned_order = order
        delivery_person.is_available = False
        delivery_person.save()

        order.delivery_partner = delivery_partner
        order.status = "out_for_delivery"
        order.save()

        return Response(
            {"message": "Order assigned successfully."},
            status=status.HTTP_200_OK
        )



class DeliveryPartnerOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type != 'delivery_partner':
            return Response({"detail": "You are not authorized to view these orders."},
                            status=status.HTTP_403_FORBIDDEN)

        latest_order_map = (
            Orders.objects
            .values('order_code')
            .annotate(latest_created=Max('created_at'))
        )

        latest_q = Q()
        for entry in latest_order_map:
            latest_q |= Q(order_code=entry['order_code'], created_at=entry['latest_created'])

        orders = Orders.objects.filter(latest_q, status__in=['confirmed', 'out_for_delivery']).order_by('-created_at')
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK) if serializer.data else Response({"detail": "No Live orders."},)