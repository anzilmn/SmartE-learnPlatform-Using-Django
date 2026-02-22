from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib import messages
from django.contrib.auth.models import User
from courses.models import Wishlist

# 1. Login Alert
@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    messages.success(request, f"Welcome back, {user.username}! Ready to level up? 🚀")

# 2. Logout Alert
@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    messages.info(request, "Logged out successfully. See you soon, vro! 👋")

# 3. Signup Alert (Hooked to your User creation)
@receiver(post_save, sender=User)
def on_user_signup(sender, instance, created, **kwargs):
    if created:
        # Note: We can't use messages here easily because we don't have the 'request' object
        # However, your signup_view already handles the redirect.
        pass

# 4. Added to Wishlist Alert
@receiver(m2m_changed, sender=Wishlist.courses.through)
def on_wishlist_change(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        # We use a custom trick here or handle this in the view. 
        # Since Signals don't always have access to 'request', 
        # standard practice for 'Added to Wishlist' is usually done in the View.
        pass