import io
import os

import requests
from django.conf import settings
from PIL import Image, ImageFont


def get_image_dimensions(site):
    if site.lower() == "facebook":
        width, height = 1200, 630
    else:  # default to X (Twitter)
        width, height = 1600, 900

    return int(width / 2), int(height / 2)


def add_watermark(img, draw, width, height):
    watermark_text = "made with osig.app"
    watermark_font = ImageFont.load_default().font_variant(size=int(height * 0.05))
    watermark_color = (255, 255, 255, 128)  # White with 50% opacity

    # Get the size of the watermark text
    bbox = watermark_font.getbbox(watermark_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position (bottom right corner)
    x = width - text_width - int(width * 0.02)
    y = height - text_height - int(height * 0.08)

    # Draw the watermark
    draw.text((x, y), watermark_text, font=watermark_font, fill=watermark_color)


def draw_wrapped_text(
    draw,
    text,
    font,
    max_width,
    y_position,
    text_spacing,
    text_color,
    width=None,
    is_title=False,
    height=None,
    align="left",
):
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
        if align == "center" and width:
            left_margin = (width - bbox[2]) // 2
        elif align == "left":
            left_margin = 0
        else:
            raise ValueError("Unsupported alignment. Use 'left' or 'center'.")

        if is_title:
            bold_offset = int(height * 0.002) if height else 1
            for offset_x in range(-bold_offset - 1, bold_offset + 1):
                for offset_y in range(-bold_offset, bold_offset + 1):
                    draw.text((left_margin + offset_x, y_position + offset_y), line, font=font, fill=text_color)
        else:
            draw.text((left_margin, y_position), line, font=font, fill=text_color)
        y_position += bbox[3] - bbox[1] + text_spacing
    return y_position


def load_font(font, size):
    if font:
        font_path = os.path.join(settings.BASE_DIR, "fonts", f"{font}.ttc")
        return ImageFont.truetype(font_path, size)
    else:
        return ImageFont.load_default().font_variant(size=size)


def create_image_buffer(img):
    buffer = io.BytesIO()
    img = img.convert("RGB")
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def load_and_resize_image(image_url, width, height):
    response = requests.get(image_url)
    img = Image.open(io.BytesIO(response.content)).convert("RGB")
    return img.resize((width, height), Image.LANCZOS)
