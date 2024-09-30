import io

from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView, UpdateView
from django_q.tasks import async_task
from PIL import Image

from core.image_styles import generate_base_image
from core.tasks import save_generated_image_to_s3
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


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
    model = User
    fields = ["first_name", "last_name", "email"]
    success_message = "User Profile Updated"
    success_url = reverse_lazy("settings")
    template_name = "pages/user-settings.html"

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        email_address = EmailAddress.objects.get_for_user(user, user.email)
        context["email_verified"] = email_address.verified
        context["resend_confirmation_url"] = reverse("resend_confirmation")

        return context


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
