from django.contrib import admin
from .models import Course, Lesson

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'price', 'created_at')
    search_fields = ('title',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)






from django.contrib import admin
from django.utils import timezone
from django.urls import reverse # Import this to get URLs by name
from .models import SupportTicket, Notification

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'created_at', 'is_resolved')
    readonly_fields = ('user', 'subject', 'message', 'created_at')
    fields = ('user', 'subject', 'message', 'admin_reply', 'is_resolved', 'created_at')

    def save_model(self, request, obj, form, change):
        # Trigger notification only if admin_reply is being added or updated
        if change and obj.admin_reply:
            # Set timestamp only if this is the first reply
            if not obj.replied_at:
                obj.replied_at = timezone.now()
            
            obj.is_resolved = True
            
            # VRO: Get the correct URL dynamically using the name from your urls.py
            support_url = reverse('contact_support')
            
            # Create Notification with the correct REDIRECT DATA
            Notification.objects.create(
                user=obj.user,
                message=f"Admin replied to your ticket: {obj.subject}",
                link=support_url, # This will now be exactly "/support/"
                notification_type='reply'
            )
            
        super().save_model(request, obj, form, change)









from django.contrib import admin
from .models import CommentReport, Profile

@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'comment_user', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('reason', 'reporter__username', 'comment__content')
    
    def comment_user(self, obj):
        return obj.comment.user.username
    comment_user.short_description = 'User Reported'

# Also register Profile if not already there to toggle 'is_blocked' manually
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_blocked', 'streak_count')
    list_editable = ('is_blocked',)