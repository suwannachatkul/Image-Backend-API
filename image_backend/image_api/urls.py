from django.urls import include, path
from rest_framework import routers
from .views import ImageListView, ImageRetrieveView, ImageUploadView, ImageUpdateView, TagListView


urlpatterns = [
    path('image/', ImageListView.as_view(), name='image-list'),
    path('image/upload/', ImageUploadView.as_view(), name='image-upload'),
    path('image/<str:pk>/', ImageRetrieveView.as_view(), name='image-retrieve'),
    path('image/<str:pk>/update', ImageUpdateView.as_view(), name='image-update'),
    path('tag/', TagListView.as_view(), name='tag-list'),
]
