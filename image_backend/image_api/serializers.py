from rest_framework import serializers
from .models import ImageInfo, Tag
from django.core.files.uploadedfile import InMemoryUploadedFile
from .util.image_util import ImageUtil
import json

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('name', 'name_slug')


class TagListingField(serializers.RelatedField):
    def to_representation(self, value):
        return value.name


class ImageSerializer(serializers.ModelSerializer):
    tags = TagListingField(many=True, read_only=True)
    class Meta:
        model = ImageInfo
        fields = ('id', 'image', 'title', 'description', 'tags')


class ImageUploadSerializer(serializers.ModelSerializer):
    MAX_SIZE = 5 * 1024 * 1024  # 1MB
    
    tags = serializers.ListField(child=serializers.CharField(max_length=50), write_only=True)
    tags_info = serializers.SerializerMethodField()

    class Meta:
        model = ImageInfo
        fields = ('image', 'title', 'description', 'tags', 'tags_info')
    
    def get_tags_info(self, obj):
        tags_data = dict(self.initial_data).get('tags', None)
        return json.dumps(tags_data).replace('\"', '')

    def validate_image(self, image):
        if image.size > self.MAX_SIZE:
            resized_image = ImageUtil.optimize_imgsize(image)         
            new_image = InMemoryUploadedFile(
                resized_image,
                None,
                image.name,
                'image/jpeg',
                resized_image.__sizeof__,
                None
            )
            if not new_image:
                raise ValidationError("Could not resize the image.")
            return new_image
        return image


    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        tags = []
        for tag_name in tags_data:
            if tag_name.strip():
                tag, created = Tag.objects.get_or_create(name=tag_name.strip())
                tags.append(tag)
        instance = ImageInfo.objects.create(**validated_data)
        instance.tags.set(tags)
        return instance

