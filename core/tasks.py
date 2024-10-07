import hashlib
import uuid

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from core.image_styles import generate_image_router
from core.models import Image
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


def save_generated_image(image, image_data):
    hash_input = "".join(
        [
            str(image_data[field])
            for field in ["profile_id", "key", "style", "site", "font", "title", "subtitle", "eyebrow", "image_url"]
        ]
    )
    image_key = hashlib.md5(hash_input.encode()).hexdigest()[:12]
    prefix = "key_" if image_data["key"] else "no_key_"
    image_key = f"{prefix}{image_key}"

    logger.info(
        "Saving image",
        image_key=image_key,
        image_data=image_data,
    )

    # Prepare the data for get_or_create
    image_fields = {
        "profile_id": image_data["profile_id"],
        "key": image_data["key"],
        "style": image_data["style"],
        "site": image_data["site"],
        "font": image_data["font"],
        "title": image_data["title"],
        "subtitle": image_data["subtitle"],
        "eyebrow": image_data["eyebrow"],
        "image_url": image_data["image_url"],
    }

    image_obj, created = Image.objects.get_or_create(**image_fields)

    image_filename = f"{image_key}.png"
    image_content = ContentFile(image.getvalue())
    image_obj.generated_image.save(image_filename, image_content, save=True)

    action = "Saved new" if created else "Updated existing"
    return f"{action} image: {image_key}"


def regenerate_and_update_image(image_id, image_data):
    logger.info("Regenerating image", image_data=image_data)
    try:
        image_obj = Image.objects.get(id=image_id)
        logger.info("Got the image to update", image_id=image_id)

        new_image = generate_image_router(image_data)
        old_image_path = image_obj.generated_image.name

        prefix = "key_" if image_data["key"] else "no_key_"
        image_filename = f"{prefix}{uuid.uuid4().hex[:12]}.png"
        image_content = ContentFile(new_image.getvalue())
        image_obj.generated_image.save(image_filename, image_content, save=True)

        if old_image_path:
            logger.info("Deleting old image", path=old_image_path)
            default_storage.delete(old_image_path)

        logger.info("Regenerated and updated image", image_id=image_id)
    except Image.DoesNotExist:
        logger.error("Image not found for regeneration", image_id=image_id)
    except Exception as e:
        logger.error("Error regenerating image", image_id=image_id, error=str(e))


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
