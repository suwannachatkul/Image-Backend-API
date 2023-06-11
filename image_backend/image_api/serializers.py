import json

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import QueryDict
from rest_framework import serializers

from .models import ImageInfo, Tag
from .util.image_util import ImageUtil


class TagSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='name')
    value = serializers.CharField(source='name_slug')
    class Meta:
        model = Tag
        fields = ('label', 'value')


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

    tags = serializers.ListField(
        child=serializers.CharField(max_length=50), write_only=True, required=False)
    tags_info = serializers.SerializerMethodField()

    class Meta:
        model = ImageInfo
        fields = ('image', 'title', 'description', 'tags', 'tags_info')

    def get_tags_info(self, obj):
        tags_data = dict(self.initial_data).get('tags', [])
        tags_data_alternate = dict(self.initial_data).get('tags[]', [])
        tags_data.extend(tags_data_alternate)
        return json.dumps(tags_data).replace('\"', '')

    def validate_image(self, image):
        if image.size > self.MAX_SIZE:
            resized_image = ImageUtil.optimize_imgsize(image)
            if not image.name.endswith(".jpg"):
                image.name = image.name.replace(
                    image.name.split(".")[-1], "jpg", 1
                )
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

    def to_internal_value(self, data):
        # handle alternate data key for tags "tags[]"
        if type(data) == QueryDict:
            tags_data = data.getlist('tags', [])
            tags_data_alternate = data.getlist('tags[]', [])
        else:
            tags_data = data.get('tags', [])
            tags_data_alternate = data.get('tags[]', [])

        if tags_data_alternate:
            tags_data.extend(tags_data_alternate)

        validated_data = super().to_internal_value(data)
        validated_data['tags'] = tags_data
        return validated_data

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
