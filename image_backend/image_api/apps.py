from django.apps import AppConfig


class ImageApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "image_api"

    def ready(self):
        import image_api.signals
