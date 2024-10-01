from django.contrib.auth.models import User
from django.db import models

from core.base_models import BaseModel
from core.utils import generate_random_key


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=10, unique=True, default=generate_random_key)

    subscription = models.ForeignKey(
        "djstripe.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The user's Stripe Subscription object, if it exists",
    )
    customer = models.ForeignKey(
        "djstripe.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The user's Stripe Customer object, if it exists",
    )
