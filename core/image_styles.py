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


def _safe_truncate(text, max_chars):
    if not text:
        return ""

    normalized_text = " ".join(str(text).split())
    if len(normalized_text) <= max_chars:
        return normalized_text

    if max_chars <= 3:
        return normalized_text[:max_chars]

    return f"{normalized_text[: max_chars - 3].rstrip()}..."


def _normalize_job_copy(title, subtitle, eyebrow):
    return (
        _safe_truncate(title, 110),
        _safe_truncate(subtitle, 180),
        _safe_truncate(eyebrow, 55),
    )


def _draw_wrapped_text_block(draw, text, font, max_width, x_position, y_position, text_color, text_spacing, **kwargs):
    if not text:
        return y_position

    is_title = kwargs.get("is_title", False)
    height = kwargs.get("height")

    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        if bbox[2] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)

    if current_line:
        lines.append(" ".join(current_line))

    for line in lines:
        bbox = font.getbbox(line)

        if is_title and height:
            bold_offset = int(height * 0.002)
            for offset_x in range(-bold_offset - 1, bold_offset + 1):
                for offset_y in range(-bold_offset, bold_offset + 1):
                    draw.text((x_position + offset_x, y_position + offset_y), line, font=font, fill=text_color)
        else:
            draw.text((x_position, y_position), line, font=font, fill=text_color)

        y_position += bbox[3] - bbox[1] + text_spacing

    return y_position


def _load_optional_image(image_url, width, height):
    if not image_url:
        return None

    try:
        return load_and_resize_image(image_url, width, height)
    except Exception as e:
        logger.warning("Failed to load remote image", image_url=image_url, error=str(e))
        return None


def generate_image_router(image_data):
    style = image_data.get("style", "base")
    image_url = image_data.get("image_url") or image_data.get("image_or_logo")

    common_kwargs = {
        "profile_id": image_data.get("profile_id"),
        "site": image_data.get("site"),
        "font": image_data.get("font"),
        "title": image_data.get("title"),
        "subtitle": image_data.get("subtitle"),
        "output_format": image_data.get("format", "png"),
        "quality": image_data.get("quality"),
        "max_kb": image_data.get("max_kb"),
    }

    if style == "logo":
        return generate_logo_image(
            image_url=image_url,
            **common_kwargs,
        )

    if style == "job_classic":
        return generate_job_classic_image(
            eyebrow=image_data.get("eyebrow"),
            image_url=image_url,
            **common_kwargs,
        )

    if style == "job_logo":
        return generate_job_logo_image(
            eyebrow=image_data.get("eyebrow"),
            image_url=image_url,
            **common_kwargs,
        )

    if style == "job_clean":
        return generate_job_clean_image(
            eyebrow=image_data.get("eyebrow"),
            image_url=image_url,
            **common_kwargs,
        )

    return generate_base_image(
        eyebrow=image_data.get("eyebrow"),
        image_url=image_url,
        **common_kwargs,
    )


def generate_base_image(
    profile_id,
    site,
    font,
    title,
    subtitle,
    eyebrow,
    image_url,
    output_format="png",
    quality=None,
    max_kb=None,
):
    logger.info(
        "Generating base OG image",
        profile_id=profile_id,
        site=site,
        font=font,
        title=title,
        subtitle=subtitle,
        eyebrow=eyebrow,
        image_url=image_url,
    )
    has_pro_subscription = check_if_profile_has_pro_subscription(profile_id)
    width, height = get_image_dimensions(site)

    background_image = _load_optional_image(image_url, width, height)
    if background_image is not None:
        img = background_image
    else:
        img = Image.new("RGB", (width, height), color=(255, 255, 255))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 180))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    text_color = (255, 255, 255)

    title_font = load_font(font, int(height * 0.1))
    subtitle_font = load_font(font, int(height * 0.05))
    eyebrow_font = load_font(font, int(height * 0.03))

    left_margin = int(width * 0.05)
    top_margin = int(height * 0.3)
    text_spacing = int(height * 0.02)
    max_text_width = width - 2 * left_margin

    normalized_title = _safe_truncate(title.upper() if title else "", 130)
    normalized_subtitle = _safe_truncate(subtitle, 180)
    normalized_eyebrow = _safe_truncate(eyebrow.upper() if eyebrow else "", 55)

    current_y = top_margin

    if normalized_eyebrow:
        current_y = _draw_wrapped_text_block(
            draw,
            normalized_eyebrow,
            eyebrow_font,
            max_text_width,
            left_margin,
            current_y,
            text_color,
            text_spacing,
        )
        current_y += text_spacing

    if normalized_title:
        current_y = _draw_wrapped_text_block(
            draw,
            normalized_title,
            title_font,
            max_text_width,
            left_margin,
            current_y,
            text_color,
            text_spacing,
            is_title=True,
            height=height,
        )
        current_y += int(text_spacing * 3.5)

    if normalized_subtitle:
        _draw_wrapped_text_block(
            draw,
            normalized_subtitle,
            subtitle_font,
            max_text_width,
            left_margin,
            current_y,
            text_color,
            text_spacing,
        )

    if not has_pro_subscription:
        add_watermark(img, draw, width, height)

    return create_image_buffer(img, output_format=output_format, quality=quality, max_kb=max_kb)


def generate_logo_image(
    profile_id,
    site,
    font,
    title,
    subtitle,
    image_url,
    output_format="png",
    quality=None,
    max_kb=None,
):
    logger.info(
        "Generating logo OG image",
        profile_id=profile_id,
        site=site,
        font=font,
        title=title,
        subtitle=subtitle,
        image_url=image_url,
    )
    has_pro_subscription = check_if_profile_has_pro_subscription(profile_id)
    width, height = get_image_dimensions(site)

    background_color = (30, 30, 30)
    img = Image.new("RGB", (width, height), color=background_color)

    draw = ImageDraw.Draw(img)
    text_color = (255, 255, 255)

    title_font = load_font(font, int(height * 0.08))
    subtitle_font = load_font(font, int(height * 0.05))

    if image_url:
        logo = _load_optional_image(image_url, int(height * 0.4), int(height * 0.4))
        if logo is not None:
            logo = logo.convert("RGBA")

            mask = Image.new("L", logo.size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0) + logo.size, fill=255)

            logo = Image.composite(logo, Image.new("RGBA", logo.size, (0, 0, 0, 0)), mask)

            logo_x = (width - logo.width) // 2
            logo_y = int(height * 0.15)

            img.paste(logo, (logo_x, logo_y), logo)

    left_margin = int(width * 0.05)
    text_spacing = int(height * 0.02)
    max_text_width = width - 2 * left_margin

    title_y = int(height * 0.62)
    subtitle_y = int(height * 0.72)

    normalized_title = _safe_truncate(title, 90)
    normalized_subtitle = _safe_truncate(subtitle, 130)

    draw_wrapped_text(
        draw,
        normalized_title,
        title_font,
        max_text_width,
        title_y,
        text_spacing,
        text_color,
        width,
        align="center",
        is_title=True,
        height=height,
    )

    draw_wrapped_text(
        draw,
        normalized_subtitle,
        subtitle_font,
        max_text_width,
        subtitle_y,
        text_spacing,
        text_color,
        width,
        align="center",
    )

    if not has_pro_subscription:
        add_watermark(img, draw, width, height)

    return create_image_buffer(img, output_format=output_format, quality=quality, max_kb=max_kb)


def generate_job_classic_image(
    profile_id,
    site,
    font,
    title,
    subtitle,
    eyebrow,
    image_url,
    output_format="png",
    quality=None,
    max_kb=None,
):
    has_pro_subscription = check_if_profile_has_pro_subscription(profile_id)
    width, height = get_image_dimensions(site)

    background_image = _load_optional_image(image_url, width, height)
    if background_image is not None:
        img = background_image.convert("RGBA")
    else:
        img = Image.new("RGBA", (width, height), color=(24, 32, 46, 255))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 130))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    title, subtitle, eyebrow = _normalize_job_copy(title, subtitle, eyebrow)

    title_font = load_font(font, int(height * 0.09))
    subtitle_font = load_font(font, int(height * 0.05))
    eyebrow_font = load_font(font, int(height * 0.032))

    left_margin = int(width * 0.08)
    current_y = int(height * 0.22)
    max_text_width = int(width * 0.84)
    text_spacing = int(height * 0.016)

    text_color = (255, 255, 255)

    if eyebrow:
        current_y = _draw_wrapped_text_block(
            draw,
            eyebrow.upper(),
            eyebrow_font,
            max_text_width,
            left_margin,
            current_y,
            text_color,
            text_spacing,
        )
        current_y += int(height * 0.02)

    if title:
        current_y = _draw_wrapped_text_block(
            draw,
            title,
            title_font,
            max_text_width,
            left_margin,
            current_y,
            text_color,
            text_spacing,
            is_title=True,
            height=height,
        )
        current_y += int(height * 0.03)

    if subtitle:
        _draw_wrapped_text_block(
            draw,
            subtitle,
            subtitle_font,
            max_text_width,
            left_margin,
            current_y,
            text_color,
            text_spacing,
        )

    if not has_pro_subscription:
        add_watermark(img, draw, width, height)

    return create_image_buffer(img, output_format=output_format, quality=quality, max_kb=max_kb)


def generate_job_logo_image(
    profile_id,
    site,
    font,
    title,
    subtitle,
    eyebrow,
    image_url,
    output_format="png",
    quality=None,
    max_kb=None,
):
    has_pro_subscription = check_if_profile_has_pro_subscription(profile_id)
    width, height = get_image_dimensions(site)

    img = Image.new("RGB", (width, height), color=(17, 24, 39))
    draw = ImageDraw.Draw(img)

    title, subtitle, eyebrow = _normalize_job_copy(title, subtitle, eyebrow)

    title_font = load_font(font, int(height * 0.085))
    subtitle_font = load_font(font, int(height * 0.05))
    eyebrow_font = load_font(font, int(height * 0.03))

    left_margin = int(width * 0.08)
    max_text_width = int(width * 0.6)
    text_spacing = int(height * 0.016)
    current_y = int(height * 0.2)

    if eyebrow:
        current_y = _draw_wrapped_text_block(
            draw,
            eyebrow.upper(),
            eyebrow_font,
            max_text_width,
            left_margin,
            current_y,
            (147, 197, 253),
            text_spacing,
        )
        current_y += int(height * 0.015)

    if title:
        current_y = _draw_wrapped_text_block(
            draw,
            title,
            title_font,
            max_text_width,
            left_margin,
            current_y,
            (255, 255, 255),
            text_spacing,
            is_title=True,
            height=height,
        )
        current_y += int(height * 0.02)

    if subtitle:
        _draw_wrapped_text_block(
            draw,
            subtitle,
            subtitle_font,
            max_text_width,
            left_margin,
            current_y,
            (209, 213, 219),
            text_spacing,
        )

    logo_size = int(height * 0.42)
    logo_x = width - logo_size - int(width * 0.08)
    logo_y = int(height * 0.15)

    logo = _load_optional_image(image_url, logo_size, logo_size)
    if logo is not None:
        logo = logo.convert("RGBA")

        mask = Image.new("L", logo.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + logo.size, fill=255)
        logo = Image.composite(logo, Image.new("RGBA", logo.size, (0, 0, 0, 0)), mask)

        img.paste(logo, (logo_x, logo_y), logo)
    else:
        placeholder_box = [
            logo_x,
            logo_y,
            logo_x + logo_size,
            logo_y + logo_size,
        ]
        draw.ellipse(placeholder_box, outline=(75, 85, 99), width=4)
        draw.text(
            (logo_x + int(logo_size * 0.24), logo_y + int(logo_size * 0.44)),
            "LOGO",
            fill=(107, 114, 128),
            font=load_font(font, int(height * 0.03)),
        )

    if not has_pro_subscription:
        add_watermark(img, draw, width, height)

    return create_image_buffer(img, output_format=output_format, quality=quality, max_kb=max_kb)


def generate_job_clean_image(
    profile_id,
    site,
    font,
    title,
    subtitle,
    eyebrow,
    image_url,
    output_format="png",
    quality=None,
    max_kb=None,
):
    has_pro_subscription = check_if_profile_has_pro_subscription(profile_id)
    width, height = get_image_dimensions(site)

    img = Image.new("RGB", (width, height), color=(250, 250, 252))
    draw = ImageDraw.Draw(img)

    title, subtitle, eyebrow = _normalize_job_copy(title, subtitle, eyebrow)

    title_font = load_font(font, int(height * 0.082))
    subtitle_font = load_font(font, int(height * 0.048))
    eyebrow_font = load_font(font, int(height * 0.028))

    accent_width = int(width * 0.018)
    draw.rectangle([0, 0, accent_width, height], fill=(37, 99, 235))

    content_left = accent_width + int(width * 0.06)
    max_text_width = int(width * 0.62)
    text_spacing = int(height * 0.014)
    current_y = int(height * 0.22)

    if eyebrow:
        current_y = _draw_wrapped_text_block(
            draw,
            eyebrow.upper(),
            eyebrow_font,
            max_text_width,
            content_left,
            current_y,
            (37, 99, 235),
            text_spacing,
        )
        current_y += int(height * 0.012)

    if title:
        current_y = _draw_wrapped_text_block(
            draw,
            title,
            title_font,
            max_text_width,
            content_left,
            current_y,
            (17, 24, 39),
            text_spacing,
            is_title=True,
            height=height,
        )
        current_y += int(height * 0.018)

    if subtitle:
        _draw_wrapped_text_block(
            draw,
            subtitle,
            subtitle_font,
            max_text_width,
            content_left,
            current_y,
            (55, 65, 81),
            text_spacing,
        )

    logo_size = int(height * 0.28)
    logo_x = width - logo_size - int(width * 0.08)
    logo_y = int(height * 0.34)
    logo = _load_optional_image(image_url, logo_size, logo_size)
    if logo is not None:
        img.paste(logo.convert("RGB"), (logo_x, logo_y))
    else:
        draw.rectangle(
            [
                logo_x,
                logo_y,
                logo_x + logo_size,
                logo_y + logo_size,
            ],
            outline=(209, 213, 219),
            width=3,
        )

    if not has_pro_subscription:
        add_watermark(img, draw, width, height)

    return create_image_buffer(img, output_format=output_format, quality=quality, max_kb=max_kb)
