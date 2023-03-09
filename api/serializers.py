from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import serializers, exceptions
from .models import User, Image, TempLink
from sorl.thumbnail import get_thumbnail
from .utils import generate_token


class UserPrivateSerializer(serializers.ModelSerializer):
    """
    Serializer for showing account details it's owner.
    """

    class Meta:
        model = User

        fields = (
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'account_tier'
        )

        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }
    

class UserPublicSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for user data presentation for other users. Restricts
    amount of data shown.
    """

    url = serializers.HyperlinkedIdentityField(view_name='user-detail')

    class Meta:
        model = User

        fields = (
            'id',
            'url',
            'username',
            'email',
        )


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for listing and uploading images.
    Must be used by authenticated users only.
    """

    url = serializers.HyperlinkedIdentityField(view_name='image-detail')

    class Meta:
        model = Image

        fields = (
            'pk',
            'image',
            'url',
        )

        extra_kwargs = {
            'image': {
                'write_only': True
            }
        }

    def create(self, validated_data):
        """
        Creates new image instance. Appends reuqest.user as owner.
        """
        request = self.context.get('request')

        # Make sure this was called by authenticated user.
        assert request.user.is_authenticated, (
            'Only authenticated users can upload images.'
        )

        # Create instance.
        instance = Image.objects.create(
            **validated_data,
            owner=request.user
        )
        instance.save()
        return instance
    

class ImageDetailSerializer(ImageSerializer):
    """
    Serializer for accessing image details.
    Details depend on owner's account tier's properties.
    """

    class Meta:
        model = Image

        fields = (
            'pk',
            'image',
        )

    def to_representation(self, instance):
        """
        Make sure returned data is trimmed in accordance with
        image owner's account tier settings.
        """
        request = self.context.get('request')
        result = super().to_representation(instance)
        account = instance.owner.account_tier

        # Decide whether to preserve original image link.
        if not account.show_original:
            del result['image']
        
        # Add absolute urls to thumbnails of predefined sizes.
        for size in account.thumbnail_sizes.all():
            thumbnail = get_thumbnail(
                instance.image, 
                f"x{size.height}", 
                quality=50
            )
            result[f"thumbnail-{size.height}px"] = (
                request.build_absolute_uri(thumbnail.url))
            
        # Add URL to temporary links.
        if account.can_generate_temp_link:
            relative_url = reverse(
                'templink-list-create', 
                kwargs={'image_pk': instance.pk}
            )
            result['templink'] = request.build_absolute_uri(relative_url)
        
        return result
    
    def create(self, validated_data):
        raise exceptions.PermissionDenied((
            "Upload through ImageDetailSerializer is prohibited. " +
            "Use base image serializer instead."
        ))
    

class TempLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for temporary links. Replaces token with full URL.
    """

    link = serializers.URLField(read_only=True)

    class Meta:
        model = TempLink

        fields = (
            'pk',
            'link',
            'image',
            'created',
            'expires_in',
        )

        extra_kwargs = {
            'image': {
                'read_only': True
            }
        }

    def create(self, validated_data):
        """
        Creates new TempLink instance. Appends image owner as owner.
        Generates url token.
        """
        
        view = self.context.get('view')
        image = Image.objects.get(pk=view.kwargs['image_pk'])

        token = generate_token()

        # Create and save.
        instance = TempLink.objects.create(
            **validated_data,
            token=token,
            image=image,
            owner=image.owner
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        """
        Generate representation along with full URL.
        """

        request = self.context.get('request')
        result = super().to_representation(instance)
        
        # Add link.
        result['link'] = request.build_absolute_uri((
            f'/api/templink/{instance.token}/'
        ))
        return result