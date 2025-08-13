from django.utils import timezone
from django.db import models
from django.conf import settings
from common.base import AuditMixin, StatusMixin
from user.models import User
from restaurants.models import Restaurant
import uuid
from common.types import NOTIFICATION_TYPES, PRIORITY_CHOICES

class Notification(AuditMixin, StatusMixin):
    """
    Model for storing notifications for users (both customers and restaurant owners)
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.URLField(null=True, blank=True)
    image = models.ImageField(upload_to='notifications/', null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    @classmethod
    def create_notification(cls, user, title, message, notification_type='system', **kwargs):
        """
        Helper method to create a notification
        """
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            **kwargs
        )

    @classmethod
    def send_order_notification(cls, user, order, message, **kwargs):
        """
        Send order-related notification
        """
        return cls.create_notification(
            user=user,
            title=f"Order Update: {order.order_code}",
            message=message,
            notification_type='order',
            metadata={
                'order_id': str(order.id),
                'order_code': str(order.order_code),
            },
            **kwargs
        )

    @classmethod
    def send_restaurant_notification(cls, restaurant, title, message, **kwargs):
        """
        Send notification to restaurant owner
        """
        return cls.create_notification(
            user=restaurant.owner,
            title=title,
            message=message,
            restaurant=restaurant,
            notification_type='system',
            **kwargs
        )
        
    @classmethod
    def create_async_notification(cls, user, title, message, notification_type='system', **kwargs):
        """
        Create notification asynchronously using Celery
        """
        from orders.utils import send_notification
        return send_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            **kwargs
        )

    @classmethod
    def send_async_order_notification(cls, user, order, message, **kwargs):
        """
        Send order-related notification asynchronously
        """
        from orders.utils import send_notification
        return send_notification(
            user=user,
            title=f"Order Update: {order.order_code}",
            message=message,
            notification_type='order',
            metadata={
                'order_id': str(order.id),
                'order_code': str(order.order_code),
            },
            **kwargs
        )

    @classmethod
    def send_async_restaurant_notification(cls, restaurant, title, message, **kwargs):
        """
        Send notification to restaurant owner asynchronously
        """
        from orders.utils import send_restaurant_notification
        return send_restaurant_notification(
            restaurant=restaurant,
            title=title,
            message=message,
            **kwargs
        )