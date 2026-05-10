from django.db.models import Sum
from django.utils import timezone

from .models import Category, Notification, Transaction
from .notifications import notifications_enabled


def _in_upcoming_alert_window(user, today):
    """True if user has an upcoming expense within 10 days of due date (including due date)."""
    for t in Transaction.objects.filter(
        user=user, type__iexact="expense", is_upcoming=True, due_date__isnull=False
    ):
        days_left = (t.due_date - today).days
        if 0 <= days_left <= 10:
            return True
    return False


def notification_badge(request):
    """
    Red dot on the notifications bell (Dashboard only) when there are unread
    notifications or active budget / upcoming alerts.
    """
    show = False
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"show_notification_badge": False}
    if not notifications_enabled(user):
        return {"show_notification_badge": False}

    if Notification.objects.filter(user=user, is_read=False).exists():
        show = True
    else:
        now = timezone.now()
        today = timezone.localdate()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if _in_upcoming_alert_window(user, today):
            show = True
        else:
            for cat in Category.objects.filter(user=user):
                budgeted = float(cat.budgeted or 0)
                if budgeted <= 0:
                    continue
                spent_sum = (
                    Transaction.objects.filter(
                        user=user,
                        category=cat,
                        type__iexact="expense",
                        date__gte=start_of_month,
                        date__lte=now,
                    ).aggregate(total=Sum("amount"))["total"]
                    or 0
                )
                spent_sum = float(spent_sum)
                if spent_sum / budgeted >= 0.9:
                    show = True
                    break

    return {"show_notification_badge": show}


def transaction_category_options(request):
    """
    Provide category names for transaction forms across templates.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"transaction_category_options": []}

    names = list(
        Category.objects.filter(user=user)
        .order_by("name")
        .values_list("name", flat=True)
    )
    return {"transaction_category_options": names}
