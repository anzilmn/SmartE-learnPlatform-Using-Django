from django.db import models
from django.conf import settings
from courses.models import Course # Import your course model

class ChatThread(models.Model):
    # Links a student and teacher via a specific course
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chat_threads')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_chats')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['course', 'student', 'teacher']

class Message(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True) # Changed to allow file-only messages
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False) # New field
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']