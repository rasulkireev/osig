from allauth.account.signals import email_confirmed, user_signed_up
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task

from core.models import Profile
from core.tasks import add_email_to_buttondown
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(email_confirmed)
def add_email_to_buttondown_on_confirm(sender, **kwargs):
    logger.info(
        "Adding new user to buttondown newsletter, on email confirmation",
        kwargs=kwargs,
        sender=sender,
    )
    async_task(add_email_to_buttondown, kwargs["email_address"], tag="user")


@receiver(user_signed_up)
def email_confirmation_callback(sender, request, user, **kwargs):
    if "sociallogin" in kwargs:
        logger.info(
            "Adding new user to buttondown newsletter on social signup",
            kwargs=kwargs,
            sender=sender,
        )
        email = kwargs["sociallogin"].user.email
        if email:
            async_task(add_email_to_buttondown, email, tag="user")
