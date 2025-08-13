# notifications/tasks.py
from celery import shared_task
from django.conf import settings
from restaurants.models import Restaurant
from user.models import User
from celery import shared_task
from django.core.mail import send_mail
from .models.models import Orders
from delivery.settings import DEFAULT_FROM_EMAIL
import logging
from orders.models.notification import Notification
logger = logging.getLogger(__name__)

@shared_task
def send_order_confirmation_email(order_id):
    order = Orders.objects.get(id=order_id)
    user = order.user
    
    subject = f"Order Confirmation #{order.id}"
    
    # Plain text message without HTML
    items_str = ''.join(f"{item.menu_item.name} x {item.quantity}\n" for item in order.order_items.all())
    message = f"""
    Hi {user.name},
    
    Thank you for your order (#{order.id}).
    
    Order Details:
    - Date: {order.created_at}
    - Total: ${order.total_amount}
    
    Items:
    {items_str}
    
    We'll notify you when your order ships.
    
    Best regards,
    Your Store Team
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        # No html_message parameter needed
    )
    


@shared_task
def create_in_app_notification(user_id, title, message, notification_type):
    Notification.objects.create(
        user=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )




# @shared_task
# def send_abandoned_cart_reminder():
#     from django.utils import timezone
#     from datetime import timedelta
#     from .models import Cart

#     # Find carts inactive for >1 hour
#     cutoff_time = timezone.now() - timedelta(hours=1)
#     abandoned_carts = Cart.objects.filter(
#         updated_at__lte=cutoff_time
#     ).select_related('user')

#     for cart in abandoned_carts:
#         send_mail(
#             subject="Your cart is waiting!",
#             message=f"Complete your order and get 10% OFF!",
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[cart.user.email],
#         )

@shared_task
def send_daily_promotions():
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from datetime import timedelta
    User = get_user_model()

    # Send to active users who haven't ordered today
    users = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=7)
    ).exclude(
        orders__created_at__date=timezone.now().date()
    )

    for user in users:
        send_mail(
            subject="Today's Special Offer!",
            message="Get 20% OFF your first order today!",
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        
        


@shared_task(bind=True)
def send_notification_task(self, user_id, title, message, notification_type='system', **kwargs):
    """
    Celery task to send notification asynchronously
    """
    try:
        user = User.objects.get(id=user_id)
        notification = Notification.create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            **kwargs
        )
        logger.info(f"Notification sent to {user.email}: {title}")
        return str(notification.id)
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@shared_task
def send_bulk_notifications_task(user_ids, title, message, notification_type='system', **kwargs):
    """
    Celery task to send notifications to multiple users
    """
    try:
        users = User.objects.filter(id__in=user_ids)
        notifications = []
        for user in users:
            notification = Notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                **kwargs
            )
            notifications.append(notification)

        Notification.objects.bulk_create(notifications)
        return f"Sent {len(notifications)} notifications"
    except Exception as e:
        logger.error(f"Failed to send bulk notifications: {str(e)}")
        raise

@shared_task
def send_restaurant_notification_task(restaurant_id, title, message, **kwargs):
    """
    Celery task specifically for restaurant notifications
    """
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        notification = Notification.send_restaurant_notification(
            restaurant=restaurant,
            title=title,
            message=message,
            **kwargs
        )
        return str(notification.id)
    except Exception as e:
        logger.error(f"Failed to send restaurant notification: {str(e)}")
        raise