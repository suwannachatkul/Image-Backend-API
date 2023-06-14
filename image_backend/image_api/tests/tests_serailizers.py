import os
from datetime import datetime
from io import BytesIO
from unittest import mock

from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from ..models import ImageInfo, Tag
from ..serializers import ImageSerializer, ImageUploadSerializer, TagSerializer


def create_test_image(img_size=(100, 100)):
    file = BytesIO()
    image = Image.new('RGB', img_size, 'white')
    image.save(file, 'png')
    file.name = 'test_image.png'
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type='image/png')


class TagSerializerTest(TestCase):

    def setUp(self):
        self.tag = Tag.objects.create(name='Test Tag')

    def test_tag_serializer_to_json(self):
        serialized_data = TagSerializer(self.tag).data
        self.assertEqual(serialized_data, {'label': 'Test Tag', 'value': 'test-tag'})

    def test_tag_serializer_from_json(self):
        json_data = {'label': 'Test Tag', 'value': 'test-tag'}
        deserialized_data = TagSerializer(data=json_data)
        self.assertTrue(deserialized_data.is_valid())
        self.assertEqual(deserialized_data.validated_data['name'], 'Test Tag')
        self.assertEqual(deserialized_data.validated_data['name_slug'], 'test-tag')


class ImageSerializerTest(TestCase):

    def setUp(self):
        self.tag1 = Tag.objects.create(name='Tag 1')
        self.tag2 = Tag.objects.create(name='Tag 2')

        self.image = ImageInfo.objects.create(title='Test Image', description='Test Description')
        self.image.tags.add(self.tag1, self.tag2)

    def test_image_serializer_to_json(self):
        serialized_data = ImageSerializer(self.image).data

        self.assertEqual(serialized_data['image'], None)
        self.assertEqual(serialized_data['id'], self.image.id)
        self.assertEqual(serialized_data['title'], 'Test Image')
        self.assertEqual(serialized_data['description'], 'Test Description')
        self.assertEqual(serialized_data['tags'], ['Tag 1', 'Tag 2'])

    def test_image_serializer_from_json(self):
        file_mock = create_test_image()
        json_data = {'title': 'Test Image', 'description': 'Test Description', 'image': file_mock}
        deserialized_data = ImageSerializer(data=json_data)
        self.assertTrue(deserialized_data.is_valid())
        self.assertEqual(dict(deserialized_data.validated_data), {
            'title': 'Test Image', 'description': 'Test Description', 'image': file_mock
        })

    def test_image_serializer_tags_list(self):
        serialized_data = ImageSerializer(self.image).data
        self.assertEqual(serialized_data['tags'], ['Tag 1', 'Tag 2'])


class ImageUploadSerializerTest(TestCase):

    def setUp(self):
        self.tag1 = Tag.objects.create(name='Tag 1')
        self.tag2 = Tag.objects.create(name='Tag 2')
        self.valid_image = create_test_image()
        self.valid_image_data = {
            'image': self.valid_image,
            'title': 'Test Image Title',
            'description': 'Test Image Description',
            'tags': ['Tag 1', 'Tag 2']
        }

    def test_valid_input_creates_image_object(self):
        serializer = ImageUploadSerializer(data=self.valid_image_data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        image = ImageInfo.objects.get(title='Test Image Title')
        try:
            self.assertIsNotNone(image)
            self.assertEqual(image.description, 'Test Image Description')
            self.assertCountEqual(image.tags.all(), [self.tag1, self.tag2])
        finally:
            os.remove(settings.MEDIA_ROOT + image.image.name)

    def test_tags_field_can_be_set_with_list_of_tag_names(self):
        serializer = ImageUploadSerializer(data=self.valid_image_data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        image = ImageInfo.objects.get(title='Test Image Title')
        try:
            self.assertCountEqual(image.tags.values_list('name', flat=True), ['Tag 1', 'Tag 2'])
        finally:
            os.remove(settings.MEDIA_ROOT + image.image.name)
