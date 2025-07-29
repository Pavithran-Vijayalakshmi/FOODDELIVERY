from django.db import models
from django.utils.translation import gettext_lazy as _


GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ]

USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('restaurant_owner', 'Restaurant Owner'),
        ('delivery_partner', 'Delivery Partner'),
        ('delivery_person','Delivery Person')
    ]


STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]


class DeliveryStatus(models.TextChoices):
    IDLE = 'idle', _('Idle')
    PICKED_UP = 'picked_up', _('Picked Up')
    DELIVERED = 'delivered', _('Delivered')
    RETURNED = 'returned', _('Returned')
    
    
VALID_TRANSITIONS = {
            'idle': ['picked_up'],
            'picked_up': ['delivered', 'returned'],
            'delivered': ['idle'],
            'returned': ['idle'],
        }


RESTAURANT_TYPE_CHOICES = [
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian'),
        ('both', 'Both'),
    ]

MENU_ITEM_TYPE_CHOICES = [
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian'),
        ('both', 'Both'),
    ]

PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI (e.g., Google Pay, PhonePe)'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Digital Wallet (Paytm, Amazon Pay)'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('razor_pay',"Razor Pay"),
    ]

PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Authorization'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('failed', 'Failed'),
        ('refund_initiated', 'Refund Initiated'),
        ('refunded', 'Refunded'),
    ]