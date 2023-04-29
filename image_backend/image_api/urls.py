from django.urls import path, include
from rest_framework import routers
from .views import TagListView, ImageListView, ImageRetrieveView, ImageUploadView


urlpatterns = [
    path('image/', ImageListView.as_view(), name='image-list'),    
    path('image/upload/', ImageUploadView.as_view(), name='image-upload'),
    path('image/<str:pk>/', ImageRetrieveView.as_view(), name='image-retrieve'),
    path('tag/', TagListView.as_view(), name='tag-list'),
]