from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    FileExtensionValidator,
    MinValueValidator,
    MaxValueValidator
)
from .utils import file_name_generator


class ThumbnailSize(models.Model):
    height = models.IntegerField()
 
    def __str__(self):
        return f"height {self.height}px"


class AccountTier(models.Model):
    name = models.CharField(max_length=30, unique=True)
    thumbnail_sizes = models.ManyToManyField(
        ThumbnailSize, 
        related_name='tiers_using'
    )
    show_original = models.BooleanField(default=False)
    can_generate_temp_link = models.BooleanField(default=False)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def get_default(cls):
        return cls.objects.get(default=True)
    
    class Meta:
        # Make sure there is only one default tier.
        constraints = [
            models.UniqueConstraint(
                fields=['default'],
                condition=models.Q(default=True),
                name="unique_default"
            )
        ]
    

class User(AbstractUser):
    email = models.EmailField()
    account_tier = models.ForeignKey(
        AccountTier,
        on_delete=models.PROTECT,
        related_name='users',
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.username} ({self.account_tier})"
    
    def clean(self):
        if self.account_tier is None:
            self.account_tier = AccountTier.get_default()


class Image(models.Model):
    image = models.ImageField(
        upload_to=file_name_generator,
        validators=[FileExtensionValidator(
            allowed_extensions=('jpg', 'jpeg', 'png'),
            message='Allowed file extensions: jpg/jpeg, png.'
        )],
    )
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='images'
    )

    def __str__(self):
        return f"Image {self.image.url}"
    

class TempLink(models.Model):
    token = models.CharField(max_length=45, unique=True)
    image = models.ForeignKey(
        Image, 
        on_delete=models.CASCADE, 
        related_name='templinks'
    )
    created = models.DateTimeField(auto_now_add=True)
    expires_in = models.IntegerField(
        validators=(
            MinValueValidator(300),
            MaxValueValidator(30000)
        )
    )
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='temporary_links',
    )

    def expiration_date(self):
        expires_in = timedelta(seconds=self.expires_in)
        return (self.created + expires_in)

    def has_expired(self):
        return (timezone.now() >= self.expiration_date())
    
    def __str__(self):
        return f"Templink ({'expired' if self.has_expired() else 'active'})"
    

class TempLinkTokenBlacklist(models.Model):
    token = models.CharField(max_length=45, unique=True)



