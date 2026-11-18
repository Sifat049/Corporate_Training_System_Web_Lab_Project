"""Topbar er notification bell er jonno unread count ar recent list."""
from .models import Notification


def extras(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not getattr(user, "is_approved", False):
        return {}
    qs = Notification.objects.filter(user=user)
    return {
        "unread_count": qs.filter(is_read=False).count(),
        "recent_notifications": list(qs[:5]),
    }
