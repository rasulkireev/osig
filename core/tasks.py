import uuid

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


def save_generated_image_to_s3(image):
    image_path = f"generated_images/{uuid.uuid4()}"
    logger.info("Saving user generated image to Minio", path=image_path)
    filename = f"{image_path}.png"
    file_content = ContentFile(image.getvalue())
    default_storage.save(filename, file_content)

    return f"Saved image: {image_path}"


def add_email_to_buttondown(email, tag):
    data = {
        "email": str(email),
        "metadata": {"source": tag},
        "tags": [tag],
        "referrer_url": "https://builtwithdjango.com",
        "subscriber_type": "unactivated",
    }
    if tag == "user":
        data["subscriber_type"] = "regular"

    r = requests.post(
        "https://api.buttondown.email/v1/subscribers",
        headers={"Authorization": f"Token {settings.BUTTONDOWN_API_TOKEN}"},
        json=data,
    )

    return r.json()
