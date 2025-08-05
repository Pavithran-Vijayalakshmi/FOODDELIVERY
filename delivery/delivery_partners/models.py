import re
from django.db import models
from delivery import settings
from restaurants.models import Restaurant
from django.contrib.auth import get_user_model
import uuid
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from common.types import DeliveryStatus 
from common.base import DeliveryPartnerPaymentInfoMixin

User = get_user_model()


class Delivery_Partners(DeliveryPartnerPaymentInfoMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_partner_profile')
    partner_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?\d{10,15}$', message="Enter a valid phone number")]
    )
    is_available = models.BooleanField(default=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_restaurants = models.ManyToManyField(Restaurant, related_name='delivery_partners')
    max_orders = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

    def active_orders_count(self):
        return self.orders.filter(status__in=['confirmed', 'out_for_delivery']).count()

    def has_capacity(self):
        return self.active_orders_count() < self.max_orders




class DeliveryPerson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_person_profile')
    person_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(Delivery_Partners, on_delete=models.CASCADE, related_name='delivery_persons')
    is_available = models.BooleanField(default=True)

    def validate_vehicle_number(value):
        pattern = r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$'
        if not re.match(pattern, value.upper().replace(' ', '')):
            raise ValidationError('Enter a valid vehicle number (e.g., TN01AB1234)')

    vehicle_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_vehicle_number]
    )

    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.IDLE
    )

    def __str__(self):
        return self.user.email