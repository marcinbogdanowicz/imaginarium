import os
from django.contrib.auth.management.commands.createsuperuser import (
    Command as CreateSuperUserCommand
)
from api.models import User, AccountTier


class Command(CreateSuperUserCommand):
    """
    Command for creating custom superuser with highest builtin account tier.
    Credentials should be provided same as with createsuperuser --noinput
    and they should include username, password, email.
    """

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating admin (superuser)...')

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Admin')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'imaginariumadmin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'noemail@example.com')

        try:
            tier = AccountTier.objects.get(name='Enterprise')
        except AccountTier.DoesNotExist:
            tier = AccountTier.get_default()
            self.stdout.write(
                'Enterprise tier account not created. Using default instead.'
            )

        User.objects.create_superuser(
            username=username,
            password=password,
            email=email,
            account_tier=tier
        )

        self.stdout.write('Admin created successfully.')