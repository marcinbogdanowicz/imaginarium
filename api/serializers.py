from rest_framework import serializers, exceptions
from .models import User, Image
from sorl.thumbnail import get_thumbnail


class UserPrivateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating user instance and showing account details
    to that user.
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

    def create(self, validated_data):
        """
        Creates new user instance. Makes sure password is hashed
        through django's set_password. Make sure account tier
        is set to default if none was given.
        """
        password = validated_data.pop('password', None)
        instance = User.objects.create(**validated_data)
        if password is not None:
            instance.set_password(password)
        # Clean method will set default account tier if there is none.
        instance.clean()
        instance.save()
        return instance
    

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
            'url',
        )

    def create(self, validated_data):
        """
        Creates new image instance. Appends reuqest.user as owner.
        """
        request = self.context.get('request')

        # Make sure this was called by authenticated user.
        assert (
            request.user.is_authenticated, 
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
        
        return result
    
    def create(self, validated_data):
        raise exceptions.PermissionDenied((
            "Upload through ImageDetailSerializer is prohibited. " +
            "Use base image serializer instead."
        ))