import uuid

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
