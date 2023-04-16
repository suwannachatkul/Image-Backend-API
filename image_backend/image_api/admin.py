from django.contrib import admin
from .models import ImageInfo, Tag


# Register your models here.
class ImageInfoModelAdmin(admin.ModelAdmin):
    list_display = ('image', 'title', 'get_tags', 'created_at')
    search_fields = ('image', 'title')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('tags')

    def get_tags(self, obj):
        return ",".join([tag.name for tag in obj.tags.all()])

admin.site.register(ImageInfo, ImageInfoModelAdmin)


class TagModelAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name',)

admin.site.register(Tag, TagModelAdmin)