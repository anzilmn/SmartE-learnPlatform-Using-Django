from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    thumbnail = models.ImageField(upload_to='thumbnails/')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    video_file = models.FileField(upload_to='videos/', help_text="Upload MP4 videos")
    notes_pdf = models.FileField(upload_to='notes/', blank=True, null=True)
    duration = models.CharField(max_length=10, help_text="e.g. 10:25", default="00:00") # Add this!
    order = models.PositiveIntegerField(default=0, help_text="Sequence of the lesson")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    



class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson') # One entry per student per lesson   



class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    payment_screenshot = models.ImageField(upload_to='payments/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    rejection_note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.status})"
    

class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'user') # One review per student per course

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.rating} Stars)"   


class SupportTicket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    # --- ADD THESE TWO ---
    admin_reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    # ---------------------
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.subject}"
    


class LessonCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson') # Prevent double-counting the same lesson





class Comment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    # If parent is null, it's a question. If parent has a value, it's a reply!
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField(default=False) # <--- ADD THIS FIELD

    @property
    def is_graduate(self):
        # Checks if this specific user has a certificate for the course this lesson belongs to
        return Certificate.objects.filter(user=self.user, course=self.lesson.course).exists()

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson') # One note per student per lesson



class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=100, unique=True) # For verification

    def __str__(self):
        return f"Certificate - {self.user.username} - {self.course.title}"




from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save # For auto-creating profiles
from django.dispatch import receiver

# --- NEW: PROFILE MODEL FOR AVATARS ---
from django.utils import timezone # Add this import at the top


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics/')
    bio = models.TextField(max_length=500, blank=True)
    is_blocked = models.BooleanField(default=False) # <--- ADD THIS LINE    
    total_score = models.PositiveIntegerField(default=0)
    # --- NEW TEACHER APPLICATION FIELDS ---
    is_teacher_applicant = models.BooleanField(default=False)
    certificate = models.FileField(upload_to='teacher_docs/', blank=True, null=True)
    application_status = models.CharField(
        max_length=20, 
        choices=(('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')),
        default='pending'
    )
    
    # --- STREAK FIELDS ---
    streak_count = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    longest_streak = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} Profile'

# AUTOMATION: Create a Profile every time a new User is registered
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

# --- YOUR EXISTING MODELS ---
# (Course, Lesson, Enrollment, etc. continue below...)

from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    # Updated TYPES to include chat/doubts
    TYPES = (
        ('payment', 'Payment Received'),
        ('comment', 'New Comment'),
        ('reply', 'Instructor Reply'),
        ('doubt', 'New Doubt Message'),  # Added for Student sending to Teacher
        ('chat_reply', 'Teacher Message'), # Added for Teacher replying to Student
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES, default='comment')
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True) 
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"
    



from django.db import models
from django.conf import settings


class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    courses = models.ManyToManyField('Course', related_name='wishlisted_by', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Wishlist"
    


class CommentReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    offender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 1. Auto-assign the offender when the report is created
        if self.comment and not self.offender:
            self.offender = self.comment.user

        # 2. Logic: When Admin marks the report as RESOLVED
        if self.pk:
            old_report = CommentReport.objects.get(pk=self.pk)
            if self.is_resolved and not old_report.is_resolved:
                if self.comment:
                    # PERMANENTLY hide ONLY this specific reported comment
                    self.comment.is_hidden = True
                    self.comment.save()
                    
                    # ALSO: Block the user profile
                    if hasattr(self.offender, 'profile'):
                        self.offender.profile.is_blocked = True
                        self.offender.profile.save()
                        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Report on {self.offender.username if self.offender else 'Unknown'}"









class Assessment(models.Model):
    course = models.ForeignKey(Course, related_name='assessments', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Detailed instructions for the project")
    resource_file = models.FileField(upload_to='assessment_resources/', blank=True, null=True, help_text="Template or project brief")
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    max_marks = models.PositiveIntegerField(default=100)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class AssessmentSubmission(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_submission = models.FileField(upload_to='submissions/')
    student_notes = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Grading fields
    grade = models.PositiveIntegerField(null=True, blank=True, help_text="Score out of 100")
    teacher_feedback = models.TextField(blank=True, null=True)
    is_reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.assessment.title}"