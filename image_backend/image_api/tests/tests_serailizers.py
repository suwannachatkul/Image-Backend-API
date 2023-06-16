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
from ..serializers import ImageSerializer, ImageUploadSerializer, ImageUpdateSerializer, TagSerializer


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

    def test_uploaded_image_is_not_resized_if_it_is_below_maximum_file_size(self):
        data = {
            'image': self.valid_image,
            'title': 'Test Image Title',
            'description': 'Test Image Description',
            'tags': ['Tag 1', 'Tag 2']
        }
        serializer = ImageUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        image = serializer.save()
        self.assertEqual(image.image.size, self.valid_image.size)
        os.remove(settings.MEDIA_ROOT + image.image.name)


class ImageUpdateSerializerTest(TestCase):
    def setUp(self):
        self.tag1 = Tag.objects.create(name='Tag 1')
        self.tag2 = Tag.objects.create(name='Tag 2')
        self.image = ImageInfo.objects.create(title='Test Image', description='Test Description')
        self.image.tags.add(self.tag1, self.tag2)

        self.serializer = ImageUpdateSerializer(instance=self.image)

        self.update_data = {
            "title": "New Title",
            "description": "New description",
            "tags": ["tag1", "tag2", "tag3"],
        }

    def test_valid_data(self):
        serializer = self.serializer
        serializer_data = serializer.data
        self.assertEqual(serializer_data["title"], self.image.title)
        self.assertEqual(serializer_data["description"], self.image.description)
        self.assertEqual(list(serializer_data['tags']), ['Tag 1', 'Tag 2'])

        serializer = ImageUpdateSerializer(instance=self.image, data=self.update_data)
        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.image.refresh_from_db()

        self.assertEqual(self.image.title, self.update_data["title"])
        self.assertEqual(self.image.description, self.update_data["description"])
        current_tag_list = [t.name for t in self.image.tags.all()]
        self.assertCountEqual(current_tag_list, self.update_data["tags"])
