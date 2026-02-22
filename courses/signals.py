from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # get_or_create ensures that if a profile was already made 
        # (by another process), it won't crash your site.
        Profile.objects.get_or_create(user=instance)
    
    # Save the profile every time the user is saved
    if hasattr(instance, 'profile'):
        instance.profile.save()