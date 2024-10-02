import io

import stripe
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView, UpdateView
from django_q.tasks import async_task
from djstripe import models as djstripe_models, settings as djstripe_settings
from PIL import Image

from core.forms import ProfileUpdateForm
from core.image_styles import generate_base_image
from core.models import Profile
from core.tasks import save_generated_image_to_s3
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)

stripe.api_key = djstripe_settings.djstripe_settings.STRIPE_SECRET_KEY


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site_choices"] = [("x", "X (Twitter)"), ("facebook", "Facebook")]
        context["style_choices"] = [("base", "Base")]
        context["font_choices"] = [("helvetica", "Helvetica"), ("markerfelt", "Marker Felt"), ("papyrus", "Papyrus")]
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
        success_url=request.build_absolute_uri(reverse_lazy("home")),
        cancel_url=request.build_absolute_uri(reverse_lazy("home")),
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
        return_url=request.build_absolute_uri(reverse_lazy("home")),
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
    style = request.GET.get("style", "base")
    site = request.GET.get("site", "x")
    font = request.GET.get("font")
    title = request.GET.get("title")
    subtitle = request.GET.get("subtitle")
    eyebrow = request.GET.get("eyebrow")
    image_url = request.GET.get("image_url")

    logger.info(
        "Generating image",
        site=site,
        font=font,
        title=title,
        subtitle=subtitle,
        eyebrow=eyebrow,
        image_url=image_url,
    )

    if style == "cool":
        logger.info("Printing Cool Image")
    else:
        image = generate_base_image(
            site=site,
            font=font,
            title=title,
            subtitle=subtitle,
            eyebrow=eyebrow,
            image_url=image_url,
        )

    async_task(save_generated_image_to_s3, image)

    return HttpResponse(image, content_type="image/png")
