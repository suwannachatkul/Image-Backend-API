from django.urls import include, path
from rest_framework import routers

from .views import ImageList, ImageRetrieve, ImageUploadView, TagList

urlpatterns = [
    path('image/', ImageList.as_view(), name='image-list'),    
    path('image/upload/', ImageUploadView.as_view(), name='image-upload'),
    path('image/<str:pk>/', ImageRetrieve.as_view(), name='image-retrieve'),
    path('tag/', TagList.as_view(), name='tag-list'),
]