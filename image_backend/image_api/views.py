import random
from datetime import datetime

from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ImageInfo, Tag
from .serializers import ImageSerializer, ImageUploadSerializer, TagSerializer


class TagList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ImageList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        queryset = ImageInfo.objects.all()
        # tags filter
        tags = self.request.query_params.getlist('tags[]') + self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__name__in=tags)

        # created_date filter
        created_date_exact = self.request.query_params.get('created_date')
        if created_date_exact:
            date = datetime.strptime(created_date_exact, '%Y-%m-%d')
            queryset = queryset.filter(created_at__date=date)

        # create_date range filter
        created_date_after = self.request.query_params.get('created_date__after')
        created_date_before = self.request.query_params.get('created_date__before')
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
        
        # random
        is_random = self.request.query_params.get('random')
        if is_random == 'true':
            queryset = queryset.order_by('?')

        # limit
        limit = self.request.query_params.get('limit')
        if limit:
            queryset = queryset[:int(limit)]

        return queryset


class ImageRetrieve(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ImageInfo.objects.all()
    serializer_class = ImageSerializer


class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
