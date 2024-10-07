import uuid

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q

from core.models import Image
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


def save_generated_image(image, image_data):
    existing_image = Image.objects.filter(
        Q(profile_id=image_data["profile_id"])
        & Q(key=image_data["key"])
        & Q(style=image_data["style"])
        & Q(site=image_data["site"])
        & Q(font=image_data["font"])
        & Q(title=image_data["title"])
        & Q(subtitle=image_data["subtitle"])
        & Q(eyebrow=image_data["eyebrow"])
        & Q(image_url=image_data["image_url"])
    ).first()

    prefix = "key_" if image_data["key"] else "no_key_"

    if existing_image:
        logger.info(
            "Updating image",
            image_id=existing_image.id,
            profile_id=image_data["profile_id"],
            key=image_data["key"],
            style=image_data["style"],
            site=image_data["site"],
            font=image_data["font"],
            title=image_data["title"],
            subtitle=image_data["subtitle"],
            eyebrow=image_data["eyebrow"],
            image_url=image_data["image_url"],
        )
        image_key = existing_image.generated_image.name.split("/")[-1].split(".")[0]
        if not image_key.startswith(("key_", "no_key_")):
            image_key = f"{prefix}{image_key}"
        image_filename = f"{image_key}.png"
        image_content = ContentFile(image.getvalue())
        existing_image.generated_image.save(image_filename, image_content, save=True)

        logger.info("Updated existing generated image", image_id=existing_image.id, image_key=image_key)
        return f"Updated image: {image_key}"
    else:
        image_key = f"{prefix}{uuid.uuid4().hex[:12]}"

        logger.info(
            "Saving image",
            image_key=image_key,
            profile_id=image_data["profile_id"],
            key=image_data["key"],
            style=image_data["style"],
            site=image_data["site"],
            font=image_data["font"],
            title=image_data["title"],
            subtitle=image_data["subtitle"],
            eyebrow=image_data["eyebrow"],
            image_url=image_data["image_url"],
        )

        image_obj = Image(
            profile_id=image_data["profile_id"],
            key=image_data["key"],
            style=image_data["style"],
            site=image_data["site"],
            font=image_data["font"],
            title=image_data["title"],
            subtitle=image_data["subtitle"],
            eyebrow=image_data["eyebrow"],
            image_url=image_data["image_url"],
        )

        image_filename = f"{image_key}.png"
        image_content = ContentFile(image.getvalue())
        image_obj.generated_image.save(image_filename, image_content, save=False)

        image_obj.save()

        logger.info("Saved new generated image", image_id=image_obj.id, image_key=image_key)
        return f"Saved new image: {image_key}"


def add_email_to_buttondown(email, tag):
    data = {
        "email_address": str(email),
        "metadata": {"source": tag},
        "tags": [tag],
        "referrer_url": "https://osig.app",
        "type": "regular",
    }

    r = requests.post(
        "https://api.buttondown.email/v1/subscribers",
        headers={"Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"},
        json=data,
    )

    return r.json()
