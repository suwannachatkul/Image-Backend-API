import os
from datetime import datetime
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import post_delete
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from image_api.signals import delete_image_from_s3
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, force_authenticate

from ..models import ImageInfo, Tag
from ..serializers import ImageUploadSerializer
from ..views import ImageUploadView


def create_test_image(img_size=(100, 100), file_ext='png', file_size=None):
    file = BytesIO()
    image = Image.new('RGB', img_size, 'white')
    image.save(file, file_ext)
    file.name = 'test_image.' + file_ext
    if file_size:
        file.size = file_size
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type='multipart/form-data')


class ImageAndTagGetTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', password='test')
        self.admin_group = Group.objects.create(name='admin')
        self.user.groups.add(self.admin_group)
        self.client.force_authenticate(user=self.user)

        self.image1 = ImageInfo.objects.create(title='image1', description='description1')
        self.image2 = ImageInfo.objects.create(title='image2', description='description2')
        self.tag1 = Tag.objects.create(name='tag1')
        self.tag2 = Tag.objects.create(name='tag2')
        # Create images with specific created_at dates
        self.image1.created_at = timezone.datetime(2023, 6, 1, tzinfo=timezone.get_current_timezone())
        self.image1.save()
        self.image2.created_at = timezone.datetime(2023, 6, 15, tzinfo=timezone.get_current_timezone())
        self.image2.save()

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
        self.assertTrue('tag1' in response.data[0]['tags'])

    def test_filter_image_list_by_created_date(self):
        response_exact_date = self.client.get(self.url_image_list, {'created_date': '2023-06-01'})
        self.assertEqual(response_exact_date.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_exact_date.data), 1)

        response_after = self.client.get(self.url_image_list, {'created_date__after': '2023-06-14'})
        self.assertEqual(response_after.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_after.data), 1)
        self.assertEqual(response_after.data[0]['title'], 'image2')

        response_before = self.client.get(self.url_image_list, {'created_date__before': '2023-06-02'})
        self.assertEqual(response_before.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_before.data), 1)
        self.assertEqual(response_before.data[0]['title'], 'image1')

        response_before = self.client.get(
            self.url_image_list, {
                'created_date__after': '2023-06-01', 'created_date__before': '2023-06-15'
            }
        )
        self.assertEqual(response_before.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_before.data), 2)

        response_before = self.client.get(
            self.url_image_list, {
                'created_date': '2023-06-01', 'created_date__after': '2023-06-01', 'created_date__before': '2023-06-15'
            }
        )
        self.assertEqual(response_before.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_limit_and_offset_to_image_list(self):
        # Assuming you have at least 5 images in the database
        response_off1_lim1 = self.client.get(self.url_image_list, {'limit': 1, 'offset': 1})
        self.assertEqual(response_off1_lim1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_off1_lim1.data), 1)

        response_off0_lim2 = self.client.get(self.url_image_list, {'limit': 2, 'offset': 0})
        self.assertEqual(response_off0_lim2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_off0_lim2.data), 2)

class ImageUploadTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', password='test')
        self.admin_group = Group.objects.create(name='admin')
        self.user.groups.add(self.admin_group)
        self.client.force_authenticate(user=self.user)

        self.tag1 = Tag.objects.create(name="tag1", name_slug="tag1")
        self.tag2 = Tag.objects.create(name="tag2", name_slug="tag2")

        self.url_image_upload = reverse('image-upload')

    def test_valid_image_upload(self):
        data = {
            'image': create_test_image(),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags[]': ['tag1', 'tag2']
        }
        response = self.client.post(self.url_image_upload, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        image_info = ImageInfo.objects.get(title='Test Image')
        try:
            self.assertEqual(image_info.description, 'This is a test image')
            self.assertCountEqual(image_info.tags.all(), [self.tag1, self.tag2])
        finally:
            os.remove(settings.MEDIA_ROOT + image_info.image.name)

    def test_invalid_image_upload(self):
        invalid_image_file = BytesIO()
        invalid_image_file.write(b"invalid image data")
        invalid_image_file.seek(0)
        data = {
            'image': SimpleUploadedFile('test.jpg', invalid_image_file.read(), content_type='multipart/form-data'),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags[]': ['tag1', 'tag2']
        }
        response = self.client.post(self.url_image_upload, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ImageInfo.objects.count(), 0)

    def test_image_upload_with_file_ext_param(self):
        data = {
            'image': create_test_image(),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags[]': ['tag1', 'tag2']
        }
        response = self.client.post(f"{self.url_image_upload}?file_ext=webp", data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        image_info = ImageInfo.objects.get(title='Test Image')
        try:
            image = Image.open(settings.MEDIA_ROOT + image_info.image.name)
            image.close()
            self.assertEqual(image.format.lower(), 'webp')
        finally:
            os.remove(settings.MEDIA_ROOT + image_info.image.name)

    def test_uploaded_image_is_resized_if_it_exceeds_maximum_file_size(self):
        file_size = ImageUploadView.MAX_IMG_SIZE
        width = 6000
        height = 5000
        large_image = create_test_image(img_size=(width, height), file_size=file_size + 100)
        data = {'image': large_image, 'title': 'Test Image Large'}
        response = self.client.post(self.url_image_upload, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        image_info = ImageInfo.objects.get(title='Test Image Large')
        try:
            self.assertLess(image_info.image.size, file_size)
        finally:
            os.remove(settings.MEDIA_ROOT + image_info.image.name)


class ImageUpdateTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', password='test')
        self.admin_group = Group.objects.create(name='admin')
        self.user.groups.add(self.admin_group)
        self.client.force_authenticate(user=self.user)

        self.image_info = ImageInfo.objects.create(title='Test Image', description='This is a test image')
        self.tag1 = Tag.objects.create(name="tag1", name_slug="tag1")
        self.tag2 = Tag.objects.create(name="tag2", name_slug="tag2")
        self.image_info.tags.set([self.tag1, self.tag2])

        self.url_image_update = reverse('image-update', kwargs={'pk': self.image_info.pk})

    def test_valid_image_update(self):
        data = {'title': 'New Test Image', 'description': 'This is a new test image', 'tags': ['tag1']}
        response = self.client.patch(self.url_image_update, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.image_info.refresh_from_db()
        self.assertEqual(self.image_info.title, 'New Test Image')
        self.assertEqual(self.image_info.description, 'This is a new test image')
        self.assertCountEqual(self.image_info.tags.all(), [self.tag1])


class ImageDeleteTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', password='test')
        self.admin_group = Group.objects.create(name='admin')
        self.user.groups.add(self.admin_group)
        self.client.force_authenticate(user=self.user)

        self.image_info = ImageInfo.objects.create(title='Test Image', description='This is a test image')
        self.tag1 = Tag.objects.create(name="tag1", name_slug="tag1")
        self.tag2 = Tag.objects.create(name="tag2", name_slug="tag2")
        self.image_info.tags.set([self.tag1, self.tag2])

        self.url_image_delete = reverse('image-delete', kwargs={'pk': self.image_info.pk})

        post_delete.disconnect(delete_image_from_s3, sender=ImageInfo)

    def test_image_delete(self):
        data = {'title': 'New Test Image', 'description': 'This is a new test image', 'tags': ['tag1']}
        response = self.client.delete(self.url_image_delete, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ImageInfo.objects.filter(pk=self.image_info.pk).exists())


class APIAccessTestCase(APITestCase):
    def setUp(self):
        # Create users and groups
        self.admin_group = Group.objects.create(name='admin')
        self.user_group = Group.objects.create(name='user')
        self.guest_group = Group.objects.create(name='guest')

        self.admin_user = User.objects.create_user(username='admin', password='admin')
        self.admin_user.groups.add(self.admin_group)

        self.user_user = User.objects.create_user(username='user', password='user')
        self.user_user.groups.add(self.user_group)

        self.guest_user = User.objects.create_user(username='guest', password='guest')
        self.guest_user.groups.add(self.guest_group)

        self.url_image_list = reverse('image-list')
        self.url_tag_list = reverse('tag-list')
        self.url_image_upload = reverse('image-upload')

    def test_admin_api_access(self):
        # Test access for admin user
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url_image_list)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.url_tag_list)
        self.assertEqual(response.status_code, 200)

        data = {
            'image': create_test_image(),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags[]': ['tag1', 'tag2']
        }
        response = self.client.post(self.url_image_upload, data, format='multipart')
        try:
            self.assertEqual(response.status_code, 201)
        finally:
            image_info = ImageInfo.objects.get(title='Test Image')
            os.remove(settings.MEDIA_ROOT + image_info.image.name)

    def test_user_api_access(self):
        # Test access for admin user
        self.client.force_authenticate(user=self.user_user)

        response = self.client.get(self.url_image_list)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.url_tag_list)
        self.assertEqual(response.status_code, 200)

        data = {
            'image': create_test_image(),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags[]': ['tag1', 'tag2']
        }
        response = self.client.post(self.url_image_upload, data, format='multipart')
        try:
            self.assertEqual(response.status_code, 201)
        finally:
            image_info = ImageInfo.objects.get(title='Test Image')
            os.remove(settings.MEDIA_ROOT + image_info.image.name)

    def test_guest_api_access(self):
        # Test access for guest user
        self.client.force_authenticate(user=self.guest_user)

        response = self.client.get(self.url_image_list)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.url_tag_list)
        self.assertEqual(response.status_code, 200)

        data = {
            'image': create_test_image(),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags[]': ['tag1', 'tag2']
        }
        response = self.client.post(self.url_image_upload, data, format='multipart')
        self.assertEqual(response.status_code, 403) # no permission for guest to upload

    def test_nologin_api_access(self):
        response = self.client.get(self.url_image_list)
        self.assertEqual(response.status_code, 401)

        response = self.client.get(self.url_tag_list)
        self.assertEqual(response.status_code, 401)

        data = {
            'image': create_test_image(),
            'title': 'Test Image',
            'description': 'This is a test image',
            'tags[]': ['tag1', 'tag2']
        }
        response = self.client.post(self.url_image_upload, data, format='multipart')
        self.assertEqual(response.status_code, 401)
