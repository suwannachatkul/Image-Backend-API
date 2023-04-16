from django.db import models
# from django.contrib.auth.models import User
# from rest_framework.authtoken.models import Token

# class UserToken(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     token = models.CharField(max_length=100)
#     expires_at = models.DateTimeField()

#     def is_expired(self):
#         return datetime.now() > self.expires_at