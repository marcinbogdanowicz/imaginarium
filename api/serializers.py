from rest_framework import serializers
from .models import User, Image


class UserBaseSerializer(serializers.ModelSerializer):
    """
    Base user serializer. Not to be used in views.
    """

    class Meta:
        model = User

        fields = (
            'pk',
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


class UserPrivateSerializer(UserBaseSerializer):
    """
    Serializer for creating user instance and showing account details
    to that user.
    """

    def create(self, validated_data):
        # Makes sure password is hashed through django's set_password method.
        password = validated_data.pop('password', None)
        instance = User.objects.create(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    

class UserPublicSerializer(UserBaseSerializer):
    """
    Serializer for user data presentation for other users. Restricts
    amount of data shown.
    """

    class Meta:
        model = User

        fields = (
            'pk',
            'username',
            'email',
        )
    

class ImageSerializer(serializers.ModelSerializer):
    """
    General serializer for uploaded images.
    Must be used by authenticated users only.
    """

    class Meta:
        model = Image

        fields = (
            'pk',
            'image',
        )

    def create(self, validated_data):
        # Appends request.user as owner of the image.
        # Make sure this is not AnonymousUser instance.
        request = self.context.get('request')
        instance = Image.objects.create(
            **validated_data,
            owner=request.user
        )
        instance.save()
        return instance