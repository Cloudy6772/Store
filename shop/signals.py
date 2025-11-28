from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=get_user_model())
def ensure_user_profile(sender, instance, created, **kwargs):
    """Create or update profile whenever a user is saved."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)

