from autoslug import AutoSlugField
from django.db import models

# Create your models here.

class Tag(models.Model):
    name = models.CharField(max_length=50)
    name_slug = AutoSlugField(populate_from='name')
    
    # TODO lsit of tag category

    def __str__(self):
        return self.name

class ImageInfo(models.Model):
    image = models.ImageField(
        upload_to='images/', height_field='height', width_field='width')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField(Tag)
    height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # TODO add user field

    def __str__(self):
        return self.image.name
