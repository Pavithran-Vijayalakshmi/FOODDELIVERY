from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone
from datetime import timedelta
from .models import Region, City,Country,State
from .types import GENDER_CHOICES

from .types import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES
from delivery.settings import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
import razorpay
import os
from uuid import uuid4
from django.core.validators import RegexValidator



class AuditMixinAdmin(models.Model):
    is_admin = models.BooleanField(default=False)
    admin_access_level = models.CharField(
        max_length=20,
        choices=[
            ('full', 'Full Access'),
            ('content', 'Content Management'),
            ('financial', 'Financial Reports'),
            ('support', 'Customer Support'),
        ],
        null=True,
        blank=True
    )
    admin_notes = models.TextField(blank=True, null=True)
    
    @property
    def is_staff(self):
        """Override is_staff to include admin users"""
        return self.is_admin or super().is_staff
    
    class Meta:
        abstract = True




class ProfileMixin(models.Model):
    name = models.CharField(max_length=100)
    # email = models.EmailField(unique=True)
    phone_region= models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name='profiles',
        null=True,
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True
    )
    age = models.IntegerField(null=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True)
    
    class Meta:
        abstract = True


class AuditMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated"
    )
    
    def save(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        if request and hasattr(request, 'user'):
            user = request.user
            if not self.pk and user.is_authenticated:
                self.created_by = user
            if user.is_authenticated:
                self.updated_by = user
        super().save(*args, **kwargs)

    

    class Meta:
        abstract = True

class PhoneNumberMixin(models.Model):
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name='profiles',
        null=True,
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True
    )
    
    class Meta:
        abstract = True


class AddressMixin(models.Model):
    address_line1 = models.CharField(max_length=150, blank=False, null=True)
    address_line2 = models.CharField(max_length=150, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    pincode = models.IntegerField(null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    label = models.CharField(max_length=50, help_text='e.g., Home, Work',default='Home')
    
    class Meta:
        abstract = True

class StatusMixin(models.Model):
    status = models.CharField(max_length=50, default="pending")
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

class TimeRangeMixin(models.Model):
    start_date = models.DateTimeField(default=timezone.now())
    def one_day_from_now():
        return timezone.now() + timedelta(days=1)

    end_date = models.DateTimeField(default=one_day_from_now)

    class Meta:
        abstract = True
        
        
def upload_to(instance, filename):
    # Generate unique filename
    ext = os.path.splitext(filename)[1]
    new_filename = f"{uuid4().hex}{ext}"
    # Return path based on model class name
    return f"{instance._meta.model_name}/{new_filename}"

class MediaMixin(models.Model):
    image = models.ImageField(upload_to='userProfile/', blank=True, null=True)

    class Meta:
        abstract = True
        

class PriceMixin(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        abstract = True




class ComplianceAndBankDetailsMixin(models.Model):
    # PAN Card
    pan_card = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(regex=r'^[A-Z]{5}[0-9]{4}[A-Z]$',message="Enter a valid PAN card number")],
    )

    # GST Number (optional)
    gst_number = models.CharField(
        max_length=15,
        blank=True,
        unique = True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$',
                message="Enter a valid GST number"
            )
        ]
    )

    # FSSAI License
    fssai_license = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{14}$',
                message="Enter a valid 14-digit FSSAI license number"
            )
        ],

    )

    # Images
    menu_image = models.ImageField(upload_to='restaurant/menus/', blank=True)
    profile_image = models.ImageField(upload_to='restaurant/profiles/',  blank=True)
    class Meta:
        abstract = True


from django.db import models

class RestaurantPaymentInfoMixin(models.Model):
    
    
    payout_frequency = models.CharField(
        max_length=10,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='monthly'
    )

    payment_method_preference = models.CharField(
        max_length=20,
        choices=[
            ('bank_transfer', 'Bank Transfer'),
            ('upi', 'UPI'),
        ],
        default='bank_transfer'
    )

    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,  
        help_text="Commission deducted from restaurant earnings"
    )

    class Meta:
        abstract = True


class DeliveryPartnerPaymentInfoMixin(models.Model):
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_payout = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    last_payout_date = models.DateTimeField(null=True, blank=True)
    
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Percentage of commission deducted from each payout"
    )
    is_commission_fixed = models.BooleanField(default=True, help_text="Is this a fixed or variable commission?")

    PAYOUT_CHOICES = (
        ('weekly', 'Weekly'),
        ('biweekly', 'Biweekly'),
        ('monthly', 'Monthly'),
    )
    payout_frequency = models.CharField(max_length=10, choices=PAYOUT_CHOICES, default='weekly')

    class Meta:
        abstract = True


class BankDetailsMixin(models.Model):
    account_holder_name = models.CharField(max_length=100, null = True)
    account_number = models.CharField(max_length=20, null=True)
    ifsc_code = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{4}0[A-Z0-9]{6}$',
                message="Enter a valid IFSC code"
            )
        ], null = True,
    )
    bank_name = models.CharField(max_length=100, null=True)
    upi_id = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        abstract = True
    




class PaymentMethodMixin(models.Model):
    # Core Payment Fields (unchanged)
    payment_method_id = models.UUIDField(
        default=uuid.uuid4, 
        editable=False
    )
    
    payment_method_type = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash_on_delivery'
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Razorpay-Specific Fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Transaction Identifiers (unchanged)
    gateway_reference_id = models.UUIDField(null=True, blank=True)
    merchant_reference_id = models.UUIDField(default=uuid.uuid4, editable=False)
    gateway_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps (unchanged)
    payment_authorized_at = models.DateTimeField(null=True, blank=True)
    payment_captured_at = models.DateTimeField(null=True, blank=True)
    
    # Financial Tracking (unchanged)
    amount_authorized = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    amount_captured = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    amount_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Security Fields (unchanged)
    is_live_mode = models.BooleanField(default=False)
    gateway_name = models.CharField(max_length=50, blank=True, null=True)
    
    # Audit Trail (unchanged)
    payment_attempts = models.PositiveIntegerField(default=0)
    last_error = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['gateway_reference_id']),
            models.Index(fields=['merchant_reference_id']),
        ]

    # --- Updated Methods Below ---

    def initiate_payment(self, amount, currency='INR', **kwargs):
        """Handles Razorpay Order creation or COD authorization."""
        self.amount_authorized = amount
        self.payment_attempts += 1
        self.metadata.update(kwargs)
        
        if self.payment_method_type == 'cash_on_delivery':
            self._handle_cod_authorization()
            return True
            
        elif self.payment_method_type == 'razorpay':
            return self._handle_razorpay_charge(amount, currency)
        
        return False

    def _handle_cod_authorization(self):
        """Mark COD payment as authorized."""
        self.payment_status = 'authorized'
        self.payment_authorized_at = timezone.now()
        self.save()

    def _handle_razorpay_charge(self, amount, currency):
        """Create Razorpay Order and store IDs."""
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount_in_paise = int(amount * 100)
            
            razorpay_order = client.order.create({
                'amount': amount_in_paise,
                'currency': currency,
                'payment_capture': 1,  # Auto-capture
                'notes': {
                    'merchant_reference_id': str(self.merchant_reference_id),
                }
            })
            
            # Update fields
            self.gateway_transaction_id = razorpay_order['id']
            self.gateway_reference_id = uuid.UUID(razorpay_order['id'])  # Optional
            self.razorpay_order_id = razorpay_order['id']  # If you added this field
            self.payment_status = 'authorized'
            self.payment_authorized_at = timezone.now()
            self.save()
            
            return True
            
        except Exception as e:
            self._record_failure({
                'code': 'razorpay_error',
                'message': str(e),
                'response': getattr(e, 'error', None)
            })
            return False

    def verify_razorpay_payment(self, payment_id):
        """Verify Razorpay payment via webhook/callback."""
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payment = client.payment.fetch(payment_id)
            
            if payment['status'] == 'captured':
                self.razorpay_payment_id = payment_id
                self.gateway_transaction_id = payment_id  # Optional
                self.payment_status = 'captured'
                self.payment_captured_at = timezone.now()
                self.amount_captured = payment['amount'] / 100  # Paise → INR
                self.save()
                return True
                
        except Exception as e:
            self._record_failure({
                'code': 'verification_failed',
                'message': str(e),
            })
        
        return False

    def _record_failure(self, error_details):
        """Record payment failure (unchanged)."""
        self.last_error = {
            'timestamp': timezone.now().isoformat(),
            **error_details,
        }
        self.payment_status = 'failed'
        self.save()

    # --- Helper Properties (unchanged) ---
    @property
    def is_settled(self):
        return self.payment_status in ('captured', 'refunded')

    def get_payment_debug_info(self):
        return {
            'payment_id': str(self.payment_method_id),
            'reference_id': str(self.merchant_reference_id),
            'gateway_id': self.gateway_transaction_id,
            'amounts': {
                'authorized': float(self.amount_authorized) if self.amount_authorized else None,
                'captured': float(self.amount_captured) if self.amount_captured else None,
                'refunded': float(self.amount_refunded),
            },
            'timestamps': {
                'authorized': self.payment_authorized_at.isoformat() if self.payment_authorized_at else None,
                'captured': self.payment_captured_at.isoformat() if self.payment_captured_at else None,
            }
        }
        
        
    def create_razorpay_order(self, amount):
        """Creates a Razorpay order and returns payment context"""
        try:
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET))
            receipt_id = f"ord_{str(self.id)[:30]}" 
            
            razorpay_order = client.order.create({
                'amount': int(amount * 100),  # Amount in paise
                'currency': 'INR',
                'payment_capture': 1,  # Auto-capture payment
                'receipt': receipt_id,
            })
            
            # Save Razorpay details
            self.razorpay_order_id = razorpay_order['id']
            self.payment_status = 'created'
            self.save()
            
            return {
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': 'INR',
                'key_id': RAZORPAY_KEY_ID
            }
            
        except Exception as e:
            # Log error
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Razorpay order creation failed: {str(e)}")

    def verify_razorpay_payment(self, payment_id):
        """Verifies a Razorpay payment"""
        try:
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET))
            payment = client.payment.fetch(payment_id)
            
            if payment['status'] == 'captured':
                self.razorpay_payment_id = payment_id
                self.payment_status = 'captured'
                self.payment_captured_at = timezone.now()
                self.save()
                return True
            return False
        except Exception as e:
            # Log error
            return False