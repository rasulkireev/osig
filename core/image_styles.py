from PIL import Image, ImageDraw

from core.image_utils import (
    add_watermark,
    create_image_buffer,
    draw_wrapped_text,
    get_image_dimensions,
    load_and_resize_image,
    load_font,
)
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
    width, height = get_image_dimensions(site)

    if image_url:
        img = load_and_resize_image(image_url, width, height)
    else:
        img = Image.new("RGB", (width, height), color=(255, 255, 255))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 180))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    text_color = (255, 255, 255)  # Always use white text

    title_font = load_font(font, int(height * 0.1))
    subtitle_font = load_font(font, int(height * 0.05))
    eyebrow_font = load_font(font, int(height * 0.03))

    left_margin = int(width * 0.05)
    top_margin = int(height * 0.3)
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

    current_y = top_margin
    max_text_width = width - 2 * left_margin

    if eyebrow:
        current_y = draw_wrapped_text(eyebrow.upper(), eyebrow_font, max_text_width, current_y)
        current_y += text_spacing

    if title:
        current_y = draw_wrapped_text(title.upper(), title_font, max_text_width, current_y, is_title=True)
        current_y += text_spacing * 3.5

    if subtitle:
        if len(subtitle) > 150:
            subtitle = subtitle[:147] + "..."
        draw_wrapped_text(subtitle, subtitle_font, max_text_width, current_y)

    if not has_pro_subscription:
        add_watermark(img, draw, width, height)

    return create_image_buffer(img)


def generate_logo_image(profile_id, site, font, title, subtitle, image_url):
    has_pro_subscription = check_if_profile_has_pro_subscription(profile_id)
    width, height = get_image_dimensions(site)

    background_color = (30, 30, 30)  # Almost black
    img = Image.new("RGB", (width, height), color=background_color)

    draw = ImageDraw.Draw(img)
    text_color = (255, 255, 255)  # White text

    title_font = load_font(font, int(height * 0.08))
    subtitle_font = load_font(font, int(height * 0.05))

    if image_url:
        logo = load_and_resize_image(image_url, int(height * 0.4), int(height * 0.4))
        logo = logo.convert("RGBA")

        mask = Image.new("L", logo.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + logo.size, fill=255)

        logo = Image.composite(logo, Image.new("RGBA", logo.size, (0, 0, 0, 0)), mask)

        logo_x = (width - logo.width) // 2
        logo_y = int(height * 0.15)

        img.paste(logo, (logo_x, logo_y), logo)

    # Calculate text positions and dimensions
    left_margin = int(width * 0.05)
    text_spacing = int(height * 0.02)
    max_text_width = width - 2 * left_margin

    title_y = int(height * 0.62)
    subtitle_y = int(height * 0.72)

    # Draw title with text wrapping
    title_y = draw_wrapped_text(
        draw,
        title,
        title_font,
        max_text_width,
        title_y,
        text_spacing,
        text_color,
        width,
        is_title=True,
        height=height,
        align="center",
    )

    # Draw subtitle with text wrapping
    draw_wrapped_text(
        draw, subtitle, subtitle_font, max_text_width, subtitle_y, text_spacing, text_color, width, align="center"
    )

    if not has_pro_subscription:
        add_watermark(img, draw, width, height)

    return create_image_buffer(img)
