import io
import os

import requests
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView
from PIL import Image, ImageDraw, ImageFont

from core.utils import is_dark_image
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


class HomeView(TemplateView):
    template_name = "pages/home.html"


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
    site = request.GET.get("site", "x")
    font = request.GET.get("font")
    title = request.GET.get("title")
    subtitle = request.GET.get("subtitle")
    eyebrow = request.GET.get("eyebrow")
    image_url = request.GET.get("image_url")

    if site.lower() == "facebook":
        width, height = 1200, 630
    else:  # default to X (Twitter)
        width, height = 1600, 900

    width, height = int(width / 2), int(height / 2)

    if image_url:
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        img = img.resize((width, height), Image.LANCZOS)
        text_color = (255, 255, 255) if is_dark_image(img) else (0, 0, 0)
    else:
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        text_color = (0, 0, 0)

    draw = ImageDraw.Draw(img)

    if font:
        font_path = os.path.join(settings.BASE_DIR, "fonts", f"{font}.ttc")
        title_font = ImageFont.truetype(font_path, int(height * 0.03))
        subtitle_font = ImageFont.truetype(font_path, int(height * 0.10))
        eyebrow_font = ImageFont.truetype(font_path, int(height * 0.06))
    else:
        eyebrow_font = ImageFont.load_default().font_variant(size=int(height * 0.03))
        title_font = ImageFont.load_default().font_variant(size=int(height * 0.10))
        subtitle_font = ImageFont.load_default().font_variant(size=int(height * 0.06))

    # Calculate text positions
    left_margin = int(width * 0.05)
    top_margin = int(height * 0.4)
    text_spacing = int(height * 0.02)

    current_y = top_margin

    if eyebrow:
        draw.text((left_margin, current_y), eyebrow.upper(), font=eyebrow_font, fill=text_color)
        current_y += eyebrow_font.size + text_spacing

    if title:
        draw.text((left_margin, current_y), title.upper(), font=title_font, fill=text_color)
        current_y += title_font.size + text_spacing

    if subtitle:
        draw.text((left_margin, current_y), subtitle, font=subtitle_font, fill=text_color)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer, content_type="image/png")
