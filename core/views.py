import io
from datetime import timedelta
from urllib.parse import urlencode

import stripe
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView, UpdateView
from django_q.tasks import async_task
from djstripe import models as djstripe_models, settings as djstripe_settings
from PIL import Image

from core.forms import ProfileUpdateForm
from core.image_styles import generate_image_router
from core.models import Image as ImageModel, Profile
from core.tasks import regenerate_and_update_image, save_generated_image
from core.utils import check_if_profile_has_pro_subscription
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)

stripe.api_key = djstripe_settings.djstripe_settings.STRIPE_SECRET_KEY


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site_choices"] = [("x", "X (Twitter)"), ("meta", "meta")]
        context["style_choices"] = [("base", "Base"), ("logo", "Logo")]
        context["font_choices"] = [("helvetica", "Helvetica"), ("markerfelt", "Marker Felt"), ("papyrus", "Papyrus")]

        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                context["user_key"] = profile.key
            except Profile.DoesNotExist:
                context["user_key"] = None
        else:
            context["user_key"] = None

        payment_status = self.request.GET.get("payment")
        if payment_status == "success":
            messages.success(self.request, "Thanks for subscribing, I hope you enjoy the app!")
            context["show_confetti"] = True
        elif payment_status == "failed":
            messages.error(self.request, "Something went wrong with the payment.")

        return context


class PricingView(TemplateView):
    template_name = "pages/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                context["has_pro_subscription"] = check_if_profile_has_pro_subscription(profile.id)
            except Profile.DoesNotExist:
                context["has_pro_subscription"] = False
        else:
            context["has_pro_subscription"] = False

        return context


class UserSettingsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    login_url = "account_login"
    model = Profile
    form_class = ProfileUpdateForm
    success_message = "User Profile Updated"
    success_url = reverse_lazy("settings")
    template_name = "pages/user-settings.html"

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        email_address = EmailAddress.objects.get_for_user(user, user.email)

        context["email_verified"] = email_address.verified
        context["resend_confirmation_url"] = reverse("resend_confirmation")
        context["has_pro_subscription"] = user.profile.subscription is not None

        return context


def create_checkout_session(request, pk, plan):
    user = request.user

    product = djstripe_models.Product.objects.get(name=plan)
    price = product.prices.filter(active=True).first()
    customer, _ = djstripe_models.Customer.get_or_create(subscriber=user)

    profile = user.profile
    profile.customer = customer
    profile.save(update_fields=["customer"])

    base_success_url = request.build_absolute_uri(reverse("home"))
    base_cancel_url = request.build_absolute_uri(reverse("home"))

    success_params = {"payment": "success"}
    success_url = f"{base_success_url}?{urlencode(success_params)}"

    cancel_params = {"payment": "failed"}
    cancel_url = f"{base_cancel_url}?{urlencode(cancel_params)}"

    checkout_session = stripe.checkout.Session.create(
        customer=customer.id,
        payment_method_types=["card"],
        allow_promotion_codes=True,
        automatic_tax={"enabled": True},
        line_items=[
            {
                "price": price.id,
                "quantity": 1,
            }
        ],
        mode="subscription" if plan != "one-time" else "payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_update={
            "address": "auto",
        },
        metadata={"user_id": user.id, "pk": pk, "price_id": price.id},
    )

    return redirect(checkout_session.url, code=303)


@login_required
def create_customer_portal_session(request):
    user = request.user
    customer = djstripe_models.Customer.objects.get(subscriber=user)

    session = stripe.billing_portal.Session.create(
        customer=customer.id,
        return_url=request.build_absolute_uri(reverse("home")),
    )

    return redirect(session.url, code=303)


@login_required
def resend_confirmation_email(request):
    user = request.user
    send_email_confirmation(request, user, EmailAddress.objects.get_for_user(user, user.email))

    return redirect("settings")


def blank_square_image(request):
    size = (200, 200)
    image = Image.new("RGB", size, color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_data = buffer.getvalue()
    response = HttpResponse(image_data, content_type="image/png")
    response["Content-Disposition"] = 'inline; filename="blank_square.png"'

    return response


@require_GET
def generate_image(request):
    key = request.GET.get("key", "")
    style = request.GET.get("style", "base")
    site = request.GET.get("site", "x")
    font = request.GET.get("font")
    title = request.GET.get("title")
    subtitle = request.GET.get("subtitle")
    eyebrow = request.GET.get("eyebrow")
    image_url = request.GET.get("image_url")

    profile_id = None
    try:
        profile_id = Profile.objects.get(key=key).id
    except Profile.DoesNotExist:
        logger.error("Profile Does Not Exist")

    if profile_id is None:
        style = "base"
        font = "helvetica"

    existing_image = ImageModel.objects.filter(
        Q(profile_id=profile_id)
        & Q(key=key)
        & Q(style=style)
        & Q(site=site)
        & Q(font=font)
        & Q(title=title)
        & Q(subtitle=subtitle)
        & Q(eyebrow=eyebrow)
        & Q(image_url=image_url)
    ).first()

    image_data = {
        "profile_id": profile_id,
        "key": key,
        "style": style,
        "site": site,
        "font": font,
        "title": title,
        "subtitle": subtitle,
        "eyebrow": eyebrow,
        "image_url": image_url,
    }

    if existing_image and existing_image.generated_image:
        two_days_ago = timezone.now() - timedelta(days=2)
        should_update = (settings.ENVIRONMENT == "prod" and existing_image.updated_at < two_days_ago) or (
            settings.ENVIRONMENT == "dev"
        )

        if should_update:
            async_task(regenerate_and_update_image, existing_image.id, image_data)
        else:
            logger.info("Using existing image (no update needed)", image_id=existing_image.id)

        try:
            return HttpResponse(existing_image.generated_image, content_type="image/png")
        except FileNotFoundError:
            pass

    image = generate_image_router(image_data)
    async_task(save_generated_image, image, image_data)

    return HttpResponse(image, content_type="image/png")
