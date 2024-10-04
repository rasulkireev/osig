import io
import os

import requests
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

from core.utils import check_if_profile_has_pro_subscription
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


def generate_base_image(
    profile_id,
    site,
    font,
    title,
    subtitle,
    eyebrow,
    image_url,
):
    has_pro_subscription = check_if_profile_has_pro_subscription(profile_id)

    if site.lower() == "facebook":
        width, height = 1200, 630
    else:  # default to X (Twitter)
        width, height = 1600, 900

    width, height = int(width / 2), int(height / 2)

    if image_url:
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        img = img.resize((width, height), Image.LANCZOS)
    else:
        img = Image.new("RGB", (width, height), color=(255, 255, 255))

    # Create a dark transparent overlay
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 180))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    text_color = (255, 255, 255)  # Always use white text

    if font:
        font_path = os.path.join(settings.BASE_DIR, "fonts", f"{font}.ttc")
        title_font = ImageFont.truetype(font_path, int(height * 0.1))
        subtitle_font = ImageFont.truetype(font_path, int(height * 0.05))
        eyebrow_font = ImageFont.truetype(font_path, int(height * 0.03))
    else:
        title_font = ImageFont.load_default().font_variant(size=int(height * 0.1))
        subtitle_font = ImageFont.load_default().font_variant(size=int(height * 0.05))
        eyebrow_font = ImageFont.load_default().font_variant(size=int(height * 0.03))

    # Calculate text positions
    left_margin = int(width * 0.05)
    top_margin = int(height * 0.4)
    text_spacing = int(height * 0.02)

    def draw_wrapped_text(text, font, max_width, y_position, is_title=False):
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] <= max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        for line in lines:
            bbox = font.getbbox(line)
            if is_title:
                bold_offset = int(height * 0.002)
                for offset_x in range(-bold_offset - 1, bold_offset + 1):
                    for offset_y in range(-bold_offset, bold_offset + 1):
                        draw.text((left_margin + offset_x, y_position + offset_y), line, font=font, fill=text_color)
            else:
                draw.text((left_margin, y_position), line, font=font, fill=text_color)
            y_position += bbox[3] - bbox[1] + text_spacing
        return y_position

    current_y = top_margin
    max_text_width = width - 2 * left_margin

    if eyebrow:
        current_y = draw_wrapped_text(eyebrow.upper(), eyebrow_font, max_text_width, current_y)
        current_y += text_spacing

    if title:
        current_y = draw_wrapped_text(title.upper(), title_font, max_text_width, current_y, is_title=True)
        current_y += text_spacing * 3.5

    if subtitle:
        draw_wrapped_text(subtitle, subtitle_font, max_text_width, current_y)

    if not has_pro_subscription:
        add_watermark(img, draw, width, height)

    buffer = io.BytesIO()
    img = img.convert("RGB")
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def add_watermark(img, draw, width, height):
    watermark_text = "made with osig.app"
    watermark_font = ImageFont.load_default().font_variant(size=int(height * 0.05))
    watermark_color = (255, 255, 255, 128)  # White with 50% opacity

    # Get the size of the watermark text
    bbox = watermark_font.getbbox(watermark_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position (bottom right corner)
    x = width - text_width - int(width * 0.02)  # 2% padding from right
    y = height - text_height - int(height * 0.04)  # 2% padding from bottom

    # Draw the watermark
    draw.text((x, y), watermark_text, font=watermark_font, fill=watermark_color)
