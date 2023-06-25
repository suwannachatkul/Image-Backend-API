import logging
import os

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from storages.backends.s3boto3 import S3Boto3Storage

from .models import ImageInfo

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=ImageInfo)
def delete_image_from_s3(sender, instance, **kwargs):
    logger.debug(f"image remove {instance.image.name}")
    if settings.DEBUG:
        # Delete the image file from the local directory
        image_path = instance.image.path
        if os.path.exists(image_path):
            os.remove(image_path)
    else:
        # Delete the image file from S3 using django-storages
        file_name = instance.image.name
        storage = S3Boto3Storage()
        storage.delete(file_name)
