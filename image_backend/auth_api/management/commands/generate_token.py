from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import AccessToken


class Command(BaseCommand):
    help = 'Generate JWT token for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username')
        parser.add_argument('password', type=str, help='Password')
        parser.add_argument('--exp', type=int, help='Expiration time in seconds', default=3600)

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        expiration = options['exp']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' does not exist."))
            return

        if not user.check_password(password):
            self.stdout.write(self.style.ERROR('Invalid password.'))
            return

        token = self.create_custom_token(user, expiration)
        self.stdout.write(self.style.SUCCESS(f'Token: {token}'))

    def create_custom_token(self, user, expiration):
        token = AccessToken.for_user(user)
        token.set_exp(from_time=datetime.utcnow() + timedelta(seconds=expiration))
        return str(token)
