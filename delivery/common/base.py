from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone
from datetime import timedelta
from phonenumber_field.modelfields import PhoneNumberField
from .types import GENDER_CHOICES
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .types import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES
import razorpay

class ProfileMixin(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(unique=True, region='IN')
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

class AddressMixin(models.Model):
    address_line1 = models.CharField(max_length=150, blank=False, null=True)
    address_line2 = models.CharField(max_length=150, blank=True, null=True)
    city = models.CharField(max_length=50, blank=False, null=True)
    state = models.CharField(max_length=50, blank=False,null=True)
    pincode = models.IntegerField(null=True)
    country = models.CharField(max_length=50,blank=False, null=True)
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

class MediaMixin(models.Model):
    image = models.ImageField(upload_to='media/', blank=True, null=True)

    class Meta:
        abstract = True

class PriceMixin(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        abstract = True



from django.core.validators import RegexValidator

class ComplianceAndBankDetailsMixin(models.Model):
    # PAN Card
    pan_card = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(regex=r'^[A-Z]{5}[0-9]{4}[A-Z]$',message="Enter a valid PAN card number")],
        null=True
    )

    # GST Number (optional)
    gst_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
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
        validators=[
            RegexValidator(
                regex=r'^\d{14}$',
                message="Enter a valid 14-digit FSSAI license number"
            )
        ],
        null=True
    )

    # Images
    menu_image = models.ImageField(upload_to='restaurant/menus/', null=True, blank=True)
    profile_image = models.ImageField(upload_to='restaurant/profiles/', null=True, blank=True)
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
    


import uuid
from django.db import models
from django.utils import timezone

class PaymentMethodMixin(models.Model):
    
    # Core Payment Fields
    payment_method_id = models.UUIDField(
    default=uuid.uuid4(), 
    unique=True,
    editable=False
    )
    
    payment_method_type = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash_on_delivery'
    )
    
    # Payment State Tracking
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_authorized_at = models.DateTimeField(null=True, blank=True)
    payment_captured_at = models.DateTimeField(null=True, blank=True)
    
    # Transaction Identifiers
    gateway_reference_id = models.UUIDField(null=True, blank=True)
    merchant_reference_id = models.UUIDField(default=uuid.uuid4, editable=False)
    gateway_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Security Fields
    is_live_mode = models.BooleanField(default=False)
    gateway_name = models.CharField(max_length=50, blank=True, null=True)
    
    # Financial Tracking
    amount_authorized = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    amount_captured = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    amount_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Audit Trail
    payment_attempts = models.PositiveIntegerField(default=0)
    last_error = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['gateway_reference_id']),
            models.Index(fields=['merchant_reference_id']),
        ]

    def initiate_payment(self, amount, currency='INR', **kwargs):
        """Standardized payment initiation flow"""
        self.amount_authorized = amount
        self.payment_attempts += 1
        self.metadata.update(kwargs)
        
        if self.payment_method_type == 'cash_on_delivery':
            self.payment_status = 'authorized'
            self.payment_authorized_at = timezone.now()
            self.save()
            return True
            
        # Implement gateway-specific logic:
        payment_result = self._gateway_specific_charge(amount, currency)
        
        if payment_result['status'] == 'success':
            self.gateway_transaction_id = payment_result['transaction_id']
            self.gateway_reference_id = uuid.UUID(payment_result['reference_id'])
            self.payment_status = 'authorized'
            self.payment_authorized_at = timezone.now()
            self.save()
            return True
            
        self._record_failure(payment_result)
        return False

    def capture_payment(self, amount=None):
        """Capture authorized payment"""
        if self.payment_status != 'authorized':
            return False
            
        amount_to_capture = amount or self.amount_authorized
        capture_result = self._gateway_specific_capture(amount_to_capture)
        
        if capture_result['success']:
            self.amount_captured = amount_to_capture
            self.payment_status = 'captured'
            self.payment_captured_at = timezone.now()
            self.save()
            return True
        return False

    def _gateway_specific_charge(self, amount, currency):
        """Implement actual gateway API call here"""
        # Example structure for Stripe:
        return {
            'status': 'success',
            'transaction_id': f'ch_{uuid.uuid4().hex}',
            'reference_id': uuid.uuid4().hex,
        }

    def _record_failure(self, error_details):
        self.last_error = {
            'timestamp': timezone.now().isoformat(),
            'code': error_details.get('code'),
            'message': error_details.get('message'),
            'gateway_response': error_details.get('response'),
        }
        self.payment_status = 'failed'
        self.save()

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
        
    def get_razorpay_checkout_context(self):
        """Generate context needed for Razorpay checkout.js"""
        if self.payment_method_type != 'razorpay':
            return None
            
        return {
            'key_id': settings.RAZORPAY_KEY_ID,
            'amount': int(self.amount_authorized * 100),  # Convert to paise
            'currency': 'INR',
            'order_id': self.gateway_transaction_id,
            'name': settings.COMPANY_NAME,
            'description': f'Payment for order {self.merchant_reference_id}',
            'prefill': {
                'name': self.user.get_full_name(),
                'email': self.user.email,
                'contact': getattr(self.user, 'phone_number', '')
            },
            'theme': {
                'color': '#F37254'
            }
        }

    def _gateway_specific_charge(self, amount, currency):
        """Razorpay implementation of payment charge"""
        if self.payment_method_type != 'razorpay':
            return super()._gateway_specific_charge(amount, currency)
            
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Convert amount to paise (Razorpay's requirement)
            amount_in_paise = int(amount * 100)
            
            # Create Razorpay order
            order_data = {
                'amount': amount_in_paise,
                'currency': currency,
                'payment_capture': 0,  # Authorize first, capture later
                'notes': {
                    'merchant_reference_id': str(self.merchant_reference_id),
                    'order_id': str(self.id)
                }
            }
            
            razorpay_order = client.order.create(data=order_data)
            
            return {
                'status': 'success',
                'transaction_id': razorpay_order['id'],
                'reference_id': razorpay_order['id'],
                'gateway_response': razorpay_order,
                'verification_data': {
                    'razorpay_order_id': razorpay_order['id'],
                    'callback_url': settings.RAZORPAY_WEBHOOK_URL
                }
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'code': 'razorpay_error',
                'message': str(e),
                'response': getattr(e, 'error', None)
            }

    def _gateway_specific_capture(self, amount):
        """Capture Razorpay payment"""
        if self.payment_method_type != 'razorpay':
            return super()._gateway_specific_capture(amount)
            
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount_in_paise = int(amount * 100)
            
            # First verify the payment is actually authorized
            payment = client.payment.fetch(self.gateway_transaction_id)
            if payment['status'] != 'authorized':
                return {'success': False, 'error': 'Payment not in authorized state'}
            
            # Perform capture
            capture_response = client.payment.capture(
                self.gateway_transaction_id,
                amount_in_paise
            )
            
            return {
                'success': True,
                'captured_amount': amount,
                'gateway_response': capture_response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'gateway_error': getattr(e, 'error', None)
            }