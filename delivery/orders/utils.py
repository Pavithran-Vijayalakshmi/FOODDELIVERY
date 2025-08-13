# notifications/utils.py
from .tasks import (
    send_notification_task,
    send_bulk_notifications_task,
    send_restaurant_notification_task
)

def send_notification(user, title, message, notification_type='system', **kwargs):
    """
    Helper function to trigger notification task
    """
    return send_notification_task.delay(
        user_id=user.id,
        title=title,
        message=message,
        notification_type=notification_type,
        **kwargs
    )

def send_bulk_notifications(users, title, message, notification_type='system', **kwargs):
    """
    Helper function to trigger bulk notifications
    """
    user_ids = [user.id for user in users]
    return send_bulk_notifications_task.delay(
        user_ids=user_ids,
        title=title,
        message=message,
        notification_type=notification_type,
        **kwargs
    )

def send_restaurant_notification(restaurant, title, message, **kwargs):
    """
    Helper function for restaurant-specific notifications
    """
    return send_restaurant_notification_task.delay(
        restaurant_id=restaurant.id,
        title=title,
        message=message,
        **kwargs
    )