from allauth.account.signals import email_confirmed
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(email_confirmed)
def email_confirmation_callback(sender, **kwargs):
    return  # TODO(Rasul): add addition to buttondown newsletter
    # if not settings.DEBUG:
    # add_email_to_buttondown(kwargs["email_address"], tag="user")
