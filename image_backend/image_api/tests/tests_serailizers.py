import os
from datetime import datetime
from django.test import TestCase
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from unittest import mock
from io import BytesIO
from PIL import Image

from ..models import ImageInfo, Tag
from ..serializers import TagSerializer, ImageSerializer, ImageUploadSerializer


def create_test_image(img_size=(100,100)):
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
        self.assertEqual(serialized_data, {'name': 'Test Tag', 'name_slug': 'test-tag'})

    def test_tag_serializer_from_json(self):
        json_data = {'name': 'Test Tag'}
        deserialized_data = TagSerializer(data=json_data)
        self.assertTrue(deserialized_data.is_valid())
        self.assertEqual(deserialized_data.validated_data, {'name': 'Test Tag'})


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
        self.assertEqual(dict(deserialized_data.validated_data), {'title': 'Test Image', 'description': 'Test Description', 'image': file_mock})

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
        self.valid_image_data2 = {
            'image': self.valid_image,
            'title': 'Test Image Title',
            'description': 'Test Image Description',
            'tags[]': ['Tag 1', 'Tag 2']
        }

    def test_valid_input_creates_image_object(self):
        serializer = ImageUploadSerializer(data=self.valid_image_data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        image = ImageInfo.objects.get(title='Test Image Title')
        self.assertIsNotNone(image)
        self.assertEqual(image.description, 'Test Image Description')
        self.assertCountEqual(image.tags.all(), [self.tag1, self.tag2])
        print(image.image.name, settings.MEDIA_ROOT + image.image.name)
        os.remove(settings.MEDIA_ROOT + image.image.name)

    def test_tags_field_can_be_set_with_list_of_tag_names(self):
        serializer = ImageUploadSerializer(data=self.valid_image_data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        image = ImageInfo.objects.get(title='Test Image Title')
        self.assertCountEqual(image.tags.values_list('name', flat=True), ['Tag 1', 'Tag 2'])
        os.remove(settings.MEDIA_ROOT + image.image.name)
    
    def test_tags_field_can_be_set_with_list_of_tag_names_with_alt_tags_key(self):
        serializer = ImageUploadSerializer(data=self.valid_image_data2)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        image = ImageInfo.objects.get(title='Test Image Title')
        self.assertCountEqual(image.tags.values_list('name', flat=True), ['Tag 1', 'Tag 2'])
        os.remove(settings.MEDIA_ROOT + image.image.name)

    def test_uploaded_image_is_resized_if_it_exceeds_maximum_file_size(self):
        large_image_file = BytesIO()
        image = Image.new('RGBA', (6000, 5000), 'white')
        image.save(large_image_file, 'png')
        large_image_file.name = 'large_image.png'
        large_image_file.size = (5 * 1024 * 1024) + 1
        init_filesize = large_image_file.size
        large_image_file.seek(0)
        data = {
            'image': SimpleUploadedFile(large_image_file.name, large_image_file.read(), content_type='image/png'),
            'title': 'Test Image Title',
            'description': 'Test Image Description',
            'tags': ['Tag 1', 'Tag 2']
        }
        serializer = ImageUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        image = serializer.save()
        self.assertLess(image.image.size, init_filesize)
        self.assertLess(image.image.size, serializer.MAX_SIZE)
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