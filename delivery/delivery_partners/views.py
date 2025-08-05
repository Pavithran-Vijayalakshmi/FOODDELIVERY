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
from common.response import api_response



class DeliveryPartnerListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        name = request.query_params.get('name')
        if name:
            partners = Delivery_Partners.objects.filter(name__icontains=name)
        else:
            partners = Delivery_Partners.objects.all()
        serializer = DeliveryPartnerSerializer(partners, many=True)
        return api_response(data=serializer.data, status_code = status.HTTP_200_OK)

class DeliveryPartnerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.user_type != 'delivery_partner':
            return api_response(message= "Only delivery partners can create a profile.", status_code=status.HTTP_403_FORBIDDEN)

        # Check if profile already exists
        if hasattr(user, 'delivery_partner_profile'):
            return api_response(message= "Profile already exists.", status_code=status.HTTP_400_BAD_REQUEST)

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

        return api_response(
            message= "Delivery partner profile created.",
            data={"partner_id": delivery_partner.partner_id}
        , status_code=status.HTTP_201_CREATED)

class DeliveryPartnerRetrieveView(APIView):
    def get(self, request):
        partner_id = request.query_params.get('id')
        if not partner_id:
            return api_response(message= "Missing 'id' in query parameters", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            partner = Delivery_Partners.objects.get(pk=partner_id)
        except Delivery_Partners.DoesNotExist:
            return api_response(message= "Not found", status_code=status.HTTP_404_NOT_FOUND)
        serializer = DeliveryPartnerSerializer(partner)
        return api_response(data=serializer.data, status_code=status.HTTP_200_OK)

class DeliveryPartnerUpdateView(APIView):
    def patch(self, request):
        partner_id = request.query_params.get('id')
        if not partner_id:
            return api_response(message= "Missing 'id' in query parameters", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            partner = Delivery_Partners.objects.get(pk=partner_id)
        except Delivery_Partners.DoesNotExist:
            return api_response(message= "Not found", status_code=status.HTTP_404_NOT_FOUND)
        serializer = DeliveryPartnerSerializer(partner, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class DeliveryPartnerDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        partner_id = request.query_params.get('id')
        if not partner_id:
            return api_response(message= "Missing 'id' in query parameters", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            partner = Delivery_Partners.objects.get(pk=partner_id)
        except Delivery_Partners.DoesNotExist:
            return api_response(message= "Not found", status_code=status.HTTP_404_NOT_FOUND)
        partner.delete()
        return api_response(status_code=status.HTTP_204_NO_CONTENT)
    

class UpdateOrderStatusByPartnerView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        
        if request.user.user_type != 'delivery_partner':
            return api_response(message= 'Only delivery partners can update this.', status_code=status.HTTP_403_FORBIDDEN)
        
        order_id = request.data.get("order_id")

        if not order_id:
            return api_response(message= "Missing order_id", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            partner = Delivery_Partners.objects.get(user=user)
        except Delivery_Partners.DoesNotExist:
            return api_response(message= "Delivery Partner not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            return api_response(message= "Order not found", status_code=status.HTTP_404_NOT_FOUND)

        if not order.assigned_person:
            return api_response(message= "No delivery person assigned to this order", status_code=status.HTTP_400_BAD_REQUEST)

        delivery_person = order.assigned_person

        if delivery_person.partner != partner:
            return api_response(message= "This delivery person does not belong to your partner account", status_code=status.HTTP_403_FORBIDDEN)

        delivery_status = delivery_person.status

        status_mapping = {
            'picked_up': 'out_for_delivery',
            'delivered': 'delivered',
            'returned': 'cancelled',
            'cash_received':'delivered'
        }
        

        new_order_status = status_mapping.get(delivery_status)
        

        if not new_order_status:
            return api_response(message= f"Cannot update order from delivery status: '{delivery_status}'"
            , status_code=status.HTTP_400_BAD_REQUEST)

        if order.status == new_order_status:
            return api_response(message= "Order is already in that status", status_code=status.HTTP_200_OK)
        if new_order_status == 'delivered':
            order.payment_status = 'paid'
        order.status = new_order_status
        order.save()

        return api_response(message= f"Order status updated to '{new_order_status}'"
        , status_code=status.HTTP_200_OK)
    
    
    
    
class DeliveryPersonCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.user_type != 'delivery_person':
            return api_response(message= "Only delivery persons can create a profile.",
                            status_code=status.HTTP_403_FORBIDDEN)

        if hasattr(user, 'delivery_person_profile'):
            return api_response(message= "Profile already exists.",
                            status_code=status.HTTP_400_BAD_REQUEST)

        data = request.data
        partner_id = data.get('partner')
        try:
            partner_instance = Delivery_Partners.objects.get(partner_id=partner_id)
        except Delivery_Partners.DoesNotExist:
            return api_response(message= "Invalid partner ID.", status_code=status.HTTP_400_BAD_REQUEST)
        
        delivery_person = DeliveryPerson.objects.create(
            user=user,
            
            person_id=data.get('person_id'),
            partner=partner_instance,
            is_available=data.get('is_available'),
            vehicle_number=data.get('vehicle_number'),
        )
        return api_response(message= "Delivery person profile created.",
                data = {"person_id": delivery_person.person_id}
            , status_code=status.HTTP_201_CREATED)


from django.db import transaction

class UpdateDeliveryPersonStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not (user.user_type == 'delivery_person' or user.is_staff or user.is_superuser):
            return api_response(
                message='Only delivery persons can update their status', 
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get("status")
        if not new_status:
            return api_response(
                message="Status is required", 
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            person = DeliveryPerson.objects.select_related('assigned_order').get(user=user)
        except DeliveryPerson.DoesNotExist:
            return api_response(
                message="Delivery Person not found", 
                status_code=status.HTTP_404_NOT_FOUND
            )

        current_status = person.status
        order = person.assigned_order
        
        # Validation checks
        if not order:
            return api_response(
                message=f"No assigned orders. Invalid transition from '{current_status}' to '{new_status}'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            return api_response(
                message=f"Invalid transition from '{current_status}' to '{new_status}'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        if new_status == 'idle' and order.status not in ['delivered', 'cancelled']:
            return api_response(
                message=f"Cannot go idle with active order (status: {order.status})",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            person.status = new_status
            
            if new_status == 'idle':
                person.is_available = True
                person.assigned_order = None
                person.save()
                
                # Only delete if you're absolutely sure this is what you want
                order.delete()
            else:
                person.save()

        return api_response(
            message=f"Delivery person status updated to '{new_status}'",
            status_code=status.HTTP_200_OK
        )
        
        
class DeliveryPersonListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if request.user.user_type != 'delivery_partner':
            return api_response(message= 'Only delivery partners can access this.', status_code=status.HTTP_403_FORBIDDEN)

        try:
            partner = user.delivery_partner_profile  
        except Delivery_Partners.DoesNotExist:
            return api_response(message= 'Delivery partner profile not found.', status_code=status.HTTP_404_NOT_FOUND)

        if partner.user != request.user:
            return api_response(message= 'You are not authorized to view delivery persons for this partner.', status_code=status.HTTP_403_FORBIDDEN)

        delivery_persons = DeliveryPerson.objects.filter(partner=partner)

        serializer = DeliveryPersonSerializer(delivery_persons, many=True)
        return api_response(data=serializer.data, status_code=status.HTTP_200_OK)
      

        
class AssignOrderToDeliveryPersonView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Verify user is a delivery partner
        if request.user.user_type != 'delivery_partner':
            return api_response(
                message= 'Only delivery partners can assign an order.', 
                status_code=status.HTTP_403_FORBIDDEN
            )

        order_id = request.data.get('order_id')
        person_id = request.data.get('person_id')

        
        # Get delivery partner profile
        try:
            delivery_partner = request.user.delivery_partner_profile
        except Delivery_Partners.DoesNotExist:
            return api_response(
                message= 'Delivery partner profile not found.',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Check partner capacity
        if not delivery_partner.has_capacity():
            return api_response(
                message= f"Maximum order limit ({delivery_partner.max_orders}) reached.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get delivery person (must belong to this partner)
        try:
            delivery_person = DeliveryPerson.objects.get(
                person_id=person_id,
                partner=delivery_partner
            )
        except DeliveryPerson.DoesNotExist:
            return api_response(
                message= "Delivery person not found or not associated with your partner account.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not delivery_person.is_available:
            return api_response(
                message= "This delivery person is not currently available.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get the order
        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            return api_response(
                message= "Order not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        
        if order.status == 'out_for_delivery':
            return api_response(
                message= "Order is already out for delivery .",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED
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
            return api_response(
                message= "No restaurants in this order are assigned to your partner account.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # For multi-restaurant orders, require specific restaurant selection
        if len(all_restaurants) > 1:
            selected_restaurant_id = request.data.get("restaurant_id")
            if not selected_restaurant_id:
                return api_response(
                    message= "Multiple restaurants detected. Please specify restaurant_id.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if UUID(selected_restaurant_id) not in partner_restaurants:
                return api_response(
                    message= "Selected restaurant is not assigned to your partner account.",
                    status_code=status.HTTP_403_FORBIDDEN
                )

        # All checks passed - assign the order
        delivery_person.assigned_order = order
        delivery_person.is_available = False
        delivery_person.save()

        order.delivery_partner = delivery_partner

        order.save()

        return api_response(
            message= "Order assigned successfully.",
            status_code=status.HTTP_200_OK
        )



class DeliveryPartnerOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type != 'delivery_partner':
            return api_response(message= "You are not authorized to view these orders.",
                            status_code=status.HTTP_403_FORBIDDEN)
        partner = user.delivery_partner_profile
        
        restaurants = partner.assigned_restaurants.all()
        
        latest_order_map = (
            Orders.objects
            .values('order_code')
            .annotate(latest_created=Max('created_at'))
        )

        latest_q = Q()
        for entry in latest_order_map:
            latest_q |= Q(order_code=entry['order_code'], created_at=entry['latest_created'])

        orders = Orders.objects.filter(
            latest_q, 
            Q(status__in=['confirmed', 'out_for_delivery']) | Q(payment_method_type__in=['cash_on_delivery'])| Q(payment_status__in = ['paid']),restaurant__in=restaurants)\
                .exclude(Q(status__in=['cancelled','delivered']))\
                .order_by('-created_at')
                
        serializer = OrderSerializer(orders, many=True)
        return api_response(data=serializer.data, status_code=status.HTTP_200_OK) if serializer.data else api_response(message= "No Live orders.",)