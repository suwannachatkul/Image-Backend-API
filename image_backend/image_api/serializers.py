import json

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
    tags = serializers.ListField(child=serializers.CharField(max_length=50), write_only=True, required=False)
    tags_info = serializers.SerializerMethodField()

    class Meta:
        model = ImageInfo
        fields = ('image', 'title', 'description', 'tags', 'tags_info')

    def get_tags_info(self, obj):
        tags_data = dict(self.initial_data).get('tags', [])
        return json.dumps(tags_data).replace('\"', '')

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
