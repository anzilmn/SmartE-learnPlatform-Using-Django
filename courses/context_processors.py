from .models import Notification

def notification_processor(request):
    if request.user.is_authenticated:
        # Get the 5 most recent notifications
        notifications = request.user.notifications.all().order_by('-created_at')[:5]
        # Count only unread ones
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {
            'notifications': notifications,
            'unread_count': unread_count
        }
    return {}



from .models import Wishlist

def wishlist_processor(request):
    if request.user.is_authenticated:
        # Get the IDs of all courses in the user's wishlist
        wishlist_obj, created = Wishlist.objects.get_or_create(user=request.user)
        wishlist_ids = wishlist_obj.courses.values_list('id', flat=True)
    else:
        wishlist_ids = []
    
    return {'wishlist_ids': wishlist_ids}




from .models import CommentReport

def report_notifications(request):
    if request.user.is_authenticated and request.user.is_superuser:
        count = CommentReport.objects.filter(is_resolved=False).count()
        return {'pending_reports_count': count}
    return {'pending_reports_count': 0}