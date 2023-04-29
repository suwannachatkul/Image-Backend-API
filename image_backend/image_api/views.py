from datetime import datetime

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .models import ImageInfo, Tag
from .serializers import ImageSerializer, TagSerializer, ImageUploadSerializer, ImageUpdateSerializer
from rest_framework.permissions import IsAuthenticated


class TagListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ImageListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        queryset = ImageInfo.objects.all()
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__name__in=tags)
        created_date = self.request.query_params.get('created_date')
        if created_date:
            date = datetime.strptime(created_date, '%Y-%m-%d')
            queryset = queryset.filter(created_at__date=date)
        return queryset


class ImageRetrieveView(generics.RetrieveAPIView):
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

class ImageUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ImageInfo.objects.all()
    serializer_class = ImageUpdateSerializer
