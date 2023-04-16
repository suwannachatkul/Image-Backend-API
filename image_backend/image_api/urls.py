from django.urls import path, include
from rest_framework import routers
from .views import TagList, ImageList, ImageRetrieve, ImageUploadView


urlpatterns = [
    path('image/', ImageList.as_view(), name='image-list'),    
    path('image/upload/', ImageUploadView.as_view(), name='image-upload'),
    path('image/<str:pk>/', ImageRetrieve.as_view(), name='image-retrieve'),
    path('tag/', TagList.as_view(), name='tag-list'),
]