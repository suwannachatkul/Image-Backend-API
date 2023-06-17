from django.urls import include, path
from rest_framework import routers
from .views import ImageListView, ImageRetrieveView, ImageUploadView, ImageUpdateView, TagListView


urlpatterns = [
    path('', ImageListView.as_view(), name='image-list'),
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('<int:pk>/', ImageRetrieveView.as_view(), name='image-retrieve'),
    path('<int:pk>/update', ImageUpdateView.as_view(), name='image-update'),
]
