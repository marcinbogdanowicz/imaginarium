from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
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
    generate_expiring_link = models.BooleanField(default=False)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def get_default(cls):
        return cls.objects.get(default=True)
    
    class Meta:
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


