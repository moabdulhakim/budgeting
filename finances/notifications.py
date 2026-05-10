from .models import Notification, NotificationPreference


def notifications_enabled(user):
    pref, _ = NotificationPreference.objects.get_or_create(user=user)
    return pref.enabled


def create_user_notification(user, message, **extra_fields):
    if not notifications_enabled(user):
        return None
    return Notification.objects.create(user=user, message=message, **extra_fields)
