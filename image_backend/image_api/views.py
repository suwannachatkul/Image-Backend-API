import json
import random
from datetime import datetime

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ImageInfo, Tag
from .serializers import ImageSerializer, ImageUpdateSerializer, ImageUploadSerializer, TagSerializer
from .util.image_util import ImageUtil


class TagListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ImageListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        queryset = ImageInfo.objects.all()

        queryset = self.__filter_by_tags(queryset)
        queryset = self.__filter_by_created_date(queryset)
        queryset = self.__order_by_random(queryset)
        queryset = self.__apply_limit_offset(queryset)

        return queryset

    def __filter_by_tags(self, queryset):
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()
        return queryset

    def __filter_by_created_date(self, queryset):
        created_date_exact = self.request.query_params.get('created_date')
        created_date_after = self.request.query_params.get('created_date__after')
        created_date_before = self.request.query_params.get('created_date__before')

        if created_date_exact:
            if created_date_after or created_date_before:
                raise ValidationError("Invalid query parameters. 'created_date' cannot be used with 'created_date__after' or 'created_date__before'.")
            date = datetime.strptime(created_date_exact, '%Y-%m-%d')
            queryset = queryset.filter(created_at__date=date)

        if created_date_after and created_date_before:
            date_after = datetime.strptime(created_date_after, '%Y-%m-%d')
            date_before = datetime.strptime(created_date_before, '%Y-%m-%d')
            queryset = queryset.filter(created_at__date__range=[date_after, date_before])
        elif created_date_after:
            date = datetime.strptime(created_date_after, '%Y-%m-%d')
            queryset = queryset.filter(created_at__date__gt=date)
        elif created_date_before:
            date = datetime.strptime(created_date_before, '%Y-%m-%d')
            queryset = queryset.filter(created_at__date__lt=date)
        return queryset

    def __order_by_random(self, queryset):
        is_random = self.request.query_params.get('random')
        if is_random == 'true':
            queryset = queryset.order_by('?')
        return queryset

    def __apply_limit_offset(self, queryset):
        limit = self.request.query_params.get('limit', None)
        offset = self.request.query_params.get('offset', 0)
        if limit:
            queryset = queryset[int(offset):int(offset) + int(limit)]
        else:
            queryset = queryset[int(offset):]
        return queryset


class ImageRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ImageInfo.objects.all()
    serializer_class = ImageSerializer


class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    SUPPORT_FILE_EXT = ["jpg", "png", "webp"]
    MAX_IMG_SIZE = 2 * 1024 * 1024  # 2MB

    def post(self, request, *args, **kwargs):
        # data
        title = request.POST.get('title')
        description = request.POST.get('description')
        tags = request.POST.getlist('tags[]')
        image = request.FILES.get('image')

        # param
        file_ext = self.request.query_params.get('file_ext')

        try:
            if file_ext:
                self.__validate_file_ext(file_ext)
            image_valid = self.__validate_image(image, transform_ext=file_ext)

        except ValidationError as error:
            return Response({'error': error.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({'error': 'Image pre-process validation error'}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'title': title,
            'description': description,
            'tags': tags,
            'image': image_valid,
        }
        serializer = ImageUploadSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def __validate_file_ext(self, file_ext):
        if file_ext not in self.SUPPORT_FILE_EXT:
            raise ValidationError(f'Not Support file_ext: {file_ext}')
        return True

    def __validate_image(self, image, transform_ext):
        # size exceeded do resize
        if image.size > self.MAX_IMG_SIZE:
            if not transform_ext:
                return self.__resize_image(image, 'jpeg', self.MAX_IMG_SIZE)
            else:
                return self.__resize_image(image, transform_ext, self.MAX_IMG_SIZE)

        # size not exceeded but image ext needed to covert
        if transform_ext and not image.name.endswith("." + transform_ext):
            image = self.__convert_image(image, transform_ext)

        return image

    def __resize_image(self, image, transform_ext, target_size):
        resized_image = ImageUtil.optimize_image_bytes_size(image.read(), transform_ext, target_size)
        return self.__create_memory_upload_file(resized_image, image.name, transform_ext)

    def __convert_image(self, image, transform_ext):
        converted_image = ImageUtil.convert_image_type(image.read(), transform_ext)
        converted_image = ImageUtil.PIL_to_bytes(converted_image, transform_ext)
        return self.__create_memory_upload_file(converted_image, image.name, transform_ext)

    def __create_memory_upload_file(self, image, image_name, ext):
        if not image_name.endswith("." + ext):
            image_name = image_name.replace(image_name.split(".")[-1], ext, 1)

        new_image = InMemoryUploadedFile(image, None, image_name, 'image/' + ext, image.__sizeof__, None)
        if not new_image:
            raise ValidationError("Could not resize the image.")

        return new_image


class ImageUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ImageInfo.objects.all()
    serializer_class = ImageUpdateSerializer
