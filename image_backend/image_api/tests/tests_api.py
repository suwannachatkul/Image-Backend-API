import os
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate, APIClient


from PIL import Image
from io import BytesIO

from ..serializers import ImageUploadSerializer
from ..models import ImageInfo, Tag


def create_test_image(img_size=(100,100)):
    file = BytesIO()
    image = Image.new('RGB', img_size, 'white')
    image.save(file, 'png')
    file.name = 'test_image.png'
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type='multipart/form-data')


class ImageAndTagGetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', password='test')
        self.client.force_authenticate(user=self.user)

        self.image1 = ImageInfo.objects.create(title='image1', description='description1')
        self.image2 = ImageInfo.objects.create(title='image2', description='description2')
        self.tag1 = Tag.objects.create(name='tag1')
        self.tag2 = Tag.objects.create(name='tag2')

        self.url_image_list = reverse('image-list')
        self.url_tag_list = reverse('tag-list')

    def test_get_image_list(self):
        response = self.client.get(self.url_image_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_tag_list(self):
        response = self.client.get(self.url_tag_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_image_list_by_tags(self):
        self.image1.tags.set([self.tag1])
        self.image2.tags.set([self.tag2])
        response = self.client.get(self.url_image_list, {'tags': ['tag1']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ImageUploadTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', password='test')
        self.client.force_authenticate(user=self.user)

        self.tag1 = Tag.objects.create(name="tag1", name_slug="tag1")
        self.tag2 = Tag.objects.create(name="tag2", name_slug="tag2")

        self.url_image_upload = reverse('image-upload')
    
    def test_valid_image_upload(self):
        data = {
            'image': create_test_image(),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags': ['tag1', 'tag2']
        }
        response = self.client.post(self.url_image_upload, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        image_info = ImageInfo.objects.get(title='Test Image')
        self.assertEqual(image_info.description, 'This is a test image')
        self.assertCountEqual(image_info.tags.all(), [self.tag1, self.tag2])
        os.remove(settings.MEDIA_ROOT + image_info.image.name)
    
    def test_invalid_image_upload(self):
        invalid_image_file = BytesIO()
        invalid_image_file.write(b"invalid image data")
        invalid_image_file.seek(0)
        data = {
            'image': SimpleUploadedFile('test.jpg', invalid_image_file.read(), content_type='multipart/form-data'),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags': ['tag1', 'tag2']
        }
        response = self.client.post(self.url_image_upload, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ImageInfo.objects.count(), 0)


class ImageUpdateTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', password='test')
        self.client.force_authenticate(user=self.user)

        self.image_info = ImageInfo.objects.create(title='Test Image', description='This is a test image')
        self.tag1 = Tag.objects.create(name="tag1", name_slug="tag1")
        self.tag2 = Tag.objects.create(name="tag2", name_slug="tag2")
        self.image_info.tags.set([self.tag1, self.tag2])

        self.url_image_update = reverse('image-update', kwargs={'pk': self.image_info.pk})

    def test_valid_image_update(self):
        data = {
            'title': 'New Test Image',
            'description': 'This is a new test image',
            'tags': ['tag1']
        }
        response = self.client.patch(self.url_image_update, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.image_info.refresh_from_db()
        self.assertEqual(self.image_info.title, 'New Test Image')
        self.assertEqual(self.image_info.description, 'This is a new test image')
        self.assertCountEqual(self.image_info.tags.all(), [self.tag1])
