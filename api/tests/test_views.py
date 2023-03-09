from os import path
from shutil import rmtree
from unittest import mock
from time import sleep
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import (
    User,
    AccountTier,
    TempLink,
    TempLinkTokenBlacklist,
)
from api.serializers import (
    UserPrivateSerializer,
    UserPublicSerializer,
    TempLinkSerializer,
)

# Sample images of different formats.
SAMPLE_JPG = 'sample_jpg.jpg'
SAMPLE_PNG = 'sample_png.png'
SAMPLE_GIF = 'sample_gif.gif'
SAMPLE_BMP = 'sample_bmp.bmp'

# Temporary root for mediafiles 'uploaded' during testing.
TEMP_DIR = 'temp'
TEMP_MEDIA_ROOT = TEMP_DIR + '/media'

def tearDownModule():
    """ Destroy temporary media root after all test ran. """
    rmtree(TEMP_DIR, ignore_errors=True)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserDetailViewTestCase(APITestCase):
    """
    Tests for UserDetailView.
    """

    @classmethod
    def setUpTestData(cls):
        cls.marcin_data = {
            "username": "Marcin",
            "first_name": "Marcin",
            "last_name": "Bogdanowicz",
            "password": "Tomato789",
            "email": "marcin@example.com",
            "account_tier": None
        }
        cls.marek_data = {
            "username": "Marek",
            "password": "Toster1337",
            "email": "marek@foo.com"
        }

        cls.marcin = User.objects.create_user(**cls.marcin_data)
        cls.marek = User.objects.create_user(**cls.marek_data)

    def tearDown(self):
        self.client.logout()

    def test_returns_user_data(self):
        """
        Checks if view returns user data if request user is the user.
        Data is compared by fields defined in UserPrivateSerializer.
        """

        login(self, 'marcin_data')
        url = reverse('user-detail', kwargs={'pk': self.marcin.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data against data derived from created instance.
        # Use serializer field names to include only readable data.
        serializer_fields = get_serializer_readable_fields(UserPrivateSerializer)
        marcin_data = {
            key: getattr(self.marcin, key) for key in serializer_fields
        }
        self.assertEqual(response.data, marcin_data)

    def test_restricts_data_access_to_the_user(self):
        """
        Checks if view denies access if request user is not the user.
        """

        login(self, 'marek_data')
        url = reverse('user-detail', kwargs={'pk': self.marcin.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_404_if_no_user_in_db(self):
        """
        Checks if view returns 404 status if user does not exist.
        """

        login(self, 'marek_data')
        url = reverse('user-detail', kwargs={'pk': 12312})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserListViewTestCase(APITestCase):
    """
    Tests for UserListView view.
    """

    @classmethod
    def setUpTestData(cls):
        cls.marcin_data = {
            "username": "Marcin",
            "password": "Tomato789",
            "email": "marcin@example.com"
        }
        cls.marek_data = {
            "username": "Marek",
            "password": "Toster1337",
            "email": "marek@foo.com"
        }
        cls.jola_data = {
            "username": "Jola",
            "password": "PolaMonola777",
            "email": "jola@baz.com"
        }

        cls.marcin = User.objects.create_user(**cls.marcin_data)
        cls.marek = User.objects.create_user(**cls.marek_data)
        cls.jola = User.objects.create_user(**cls.jola_data)
    
    def setUp(self):
        """ Make sure user is logged in for each test. """
        login(self, 'marcin_data')

    def tearDown(self):
        """ Make sure user is logged out after each test. """
        self.client.logout()
    
    def test_lists_users(self):
        """
        Checks if view returns a list of users for a logged in user.
        Makes sure list contains exactly 3 users.
        """
        
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 3)

    def test_only_authenticated_access(self):
        """
        Checks if view denies access for not authenticated users.
        """

        self.client.logout()
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returns_user_public_serializer_fields(self):
        """
        Makes sure response data contains readable fields 
        defined by UserPublicSerializer.
        """

        url = reverse('user-list')
        response = self.client.get(url)
        serializer_fields = get_serializer_readable_fields(UserPublicSerializer)
        for record in response.data:
            response_fields = record.keys()
            self.assertCountEqual(response_fields, serializer_fields)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageListUploadViewTestCase(APITestCase):
    """
    Tests for ImageListUploadViewTestCase.
    """

    @classmethod
    def setUpTestData(cls):
        # Get built-in account tiers.
        cls.basic = AccountTier.objects.get(name='Basic')
        cls.premium = AccountTier.objects.get(name='Premium')
        cls.enterprise = AccountTier.objects.get(name='Enterprise')

        # Create users.
        cls.marcin_data = {
            "username": "Marcin",
            "password": "Tomato789",
            "email": "marcin@example.com",
            "account_tier": cls.enterprise
        }
        cls.marek_data = {
            "username": "Marek",
            "password": "Toster1337",
            "email": "marek@foo.com",
            "account_tier": cls.premium
        }
        cls.jola_data = {
            "username": "Jola",
            "password": "Piekarnik4445",
            "email": "jola@foo.com",
            "account_tier": cls.basic       
        }

        cls.marcin = User.objects.create_user(**cls.marcin_data)
        cls.marek = User.objects.create_user(**cls.marek_data)
        cls.jola = User.objects.create_user(**cls.jola_data)

    def tearDown(self):
        self.client.logout()

    def test_can_upload_image_in_jpeg_png(self):
        """
        Tests uploading jpeg and png images.
        """

        login(self, 'marcin_data')

        # Test jpeg.
        response = upload_image(self, SAMPLE_JPG)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test png.
        response = upload_image(self, SAMPLE_PNG)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_upload_image_in_other_formats(self):
        """
        Tests uploading formats other then jpeg or png fails.
        """

        login(self, 'marcin_data')

        # Test bmp.
        response = upload_image(self, SAMPLE_BMP)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test gif.
        response = upload_image(self, SAMPLE_GIF)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shows_only_user_images(self):
        """
        Makes sure view returns only links to requesting user's images.
        """

        # Log in as Jola.
        login(self, 'jola_data')
        
        # Upload an image.
        jola_response = upload_image(self, SAMPLE_PNG)

        # Log out and log in as Marcin.
        self.client.logout()
        login(self, 'marcin_data')
        
        # Upload twice.
        marcin_response_one = upload_image(self, SAMPLE_JPG)
        marcin_response_two = upload_image(self, SAMPLE_JPG)

        # Fetch data and assert that only 2 objects 
        # uploaded by Marcin were returned.
        url = reverse('image-list-upload')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 2)
        self.assertCountEqual(response.data, [marcin_response_one.data, marcin_response_two.data])
        self.assertNotIn(jola_response.data, response.data)

    def test_not_authenticated_user_cannot_upload_nor_list(self):
        """
        Make sure requests by non-authenticated users are not allowed.
        """

        url = reverse('image-list-upload')

        # Make a get request.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)

        # Make a post request.
        response = upload_image(self, SAMPLE_JPG)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)


@override_settings(
    THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.dbm_kvstore.KVStore',
    MEDIA_ROOT=TEMP_MEDIA_ROOT
)
class ImageDetailViewTestCase(APITestCase):
    """
    Tests for ImageDetailView view.
    """

    @classmethod
    def setUpTestData(cls):
        # Get built-in account tiers.
        cls.basic = AccountTier.objects.get(name='Basic')
        cls.premium = AccountTier.objects.get(name='Premium')
        cls.enterprise = AccountTier.objects.get(name='Enterprise')

        # Create users.
        cls.marcin_data = {
            "username": "Marcin",
            "password": "Tomato789",
            "email": "marcin@example.com",
            "account_tier": cls.enterprise
        }
        cls.marek_data = {
            "username": "Marek",
            "password": "Toster1337",
            "email": "marek@foo.com",
            "account_tier": cls.premium
        }
        cls.jola_data = {
            "username": "Jola",
            "password": "Piekarnik4445",
            "email": "jola@foo.com",
            "account_tier": cls.basic
        }

        cls.marcin = User.objects.create_user(**cls.marcin_data)
        cls.marek = User.objects.create_user(**cls.marek_data)
        cls.jola = User.objects.create_user(**cls.jola_data)

    def tearDown(self):
        self.client.logout()

    def _upload_image_and_get_response(self, user_data):
        """
        Helper function for login, image upload and request abstraction
        for following account tier tests.
        """

        # Log in as given user.
        login(self, user_data)

        # Upload image.
        img_response = upload_image(self, SAMPLE_JPG)

        # Get image details and return the response.
        url = reverse('image-detail', kwargs={'pk': img_response.data['pk']})
        return self.client.get(url)

    def test_basic_gets_small_thumbnail(self):
        """
        Confirms that user with basic account tier gets only
        a link to small 200px high thumbnail.
        """

        # Upload image and get it's detail as Basic account user.
        response = self._upload_image_and_get_response('jola_data')

        self.assertIn('thumbnail-200px', response.data)
        self.assertNotIn('thumbnail-400px', response.data)
        self.assertNotIn('image', response.data)
        self.assertNotIn('templink', response.data)

    def test_premium_gets_small_medium_thumbnail_and_original(self):
        """
        Confirms that user with premium account tier gets 200px, 400px high
        thumbnails and original image.
        """

        # Upload image and get it's detail as Premium account user.
        response = self._upload_image_and_get_response('marek_data')

        self.assertIn('thumbnail-200px', response.data)
        self.assertIn('thumbnail-400px', response.data)
        self.assertIn('image', response.data)
        self.assertNotIn('templink', response.data)

    def test_enterprise_gets_small_medium_thumbnail_original_and_templink(self):
        """
        Confirms that user with enterprise account tier gets 200px, 400px high
        thumbnails and original image.
        """

        # Upload image and get it's detail as Enterprise account user.
        response = self._upload_image_and_get_response('marcin_data')

        self.assertIn('thumbnail-200px', response.data)
        self.assertIn('thumbnail-400px', response.data)
        self.assertIn('image', response.data)
        self.assertIn('templink', response.data)

    def test_only_owner_gets_data(self):
        """
        Confirms that only image owner can get links to it.
        """

        # Upload image as Marek.
        login(self, 'marek_data')
        marek_response = upload_image(self, SAMPLE_JPG)

        # Logout and try to fetch image as Marcin.
        self.client.logout()
        login(self, 'marcin_data')
        url = reverse('image-detail', kwargs={'pk': marek_response.data['pk']})
        marcin_response = self.client.get(url)

        self.assertEqual(marcin_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', marcin_response.data)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TempLinkListCreateViewTestCase(APITestCase):
    """
    Tests for TempLinkListCreateView view.
    """

    @classmethod
    def setUpTestData(cls):
        # Get built-in account tiers.
        cls.basic = AccountTier.objects.get(name='Basic')
        cls.premium = AccountTier.objects.get(name='Premium')
        cls.enterprise = AccountTier.objects.get(name='Enterprise')

        # Create users.
        cls.marcin_data = {
            "username": "Marcin",
            "password": "Tomato789",
            "email": "marcin@example.com",
            "account_tier": cls.enterprise
        }
        cls.marek_data = {
            "username": "Marek",
            "password": "Toster1337",
            "email": "marek@foo.com",
            "account_tier": cls.enterprise
        }
        cls.jola_data = {
            "username": "Jola",
            "password": "Piekarnik4445",
            "email": "jola@foo.com",
            "account_tier": cls.basic
        }

        cls.marcin = User.objects.create_user(**cls.marcin_data)
        cls.marek = User.objects.create_user(**cls.marek_data)
        cls.jola = User.objects.create_user(**cls.jola_data)

    def tearDown(self):
        self.client.logout()
    
    def test_account_tiers(self):
        """
        Make sure account tiers have not changed:
        - basic and premium does not allow for templink creation,
        - enterprise allows for templink creation.
        """
        self.assertFalse(self.basic.can_generate_temp_link)
        self.assertFalse(self.premium.can_generate_temp_link)
        self.assertTrue(self.enterprise.can_generate_temp_link)
    
    def test_enterprise_owner_can_create_a_templink(self):
        """
        Checks that image owner with Enterprise account can create
        a templink to his image and receive templink data in return.
        """

        # Login and upload.
        login(self, 'marcin_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']

        # Create a templink.
        url = reverse('templink-list-create', kwargs={'image_pk': image_pk})
        response = self.client.post(url, {'expires_in': 1000})

        # Assert templink was created and contains serializer readable fields.
        serializer_fields = get_serializer_readable_fields(TempLinkSerializer)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), serializer_fields)

    def test_enterprise_non_owner_cannot_create_a_templink(self):
        """
        Checks that user with Enterprise account, who is not the image owner 
        cannot create a templink to such image.
        """

        # Upload image as Marcin.
        login(self, 'marcin_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']

        # Try to create a templink as Marek to Marcin's image.
        self.client.logout()
        login(self, 'marek_data')
        url = reverse('templink-list-create', kwargs={'image_pk': image_pk})
        response = self.client.post(url, {'expires_in': 1000})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)

    def test_non_enterprise_owner_cannot_create_a_templink(self):
        """
        Checks that image owner with account tier which does not allow
        for temporary link creation, will not be able to create such link
        for his image.
        """

        # Upload image as Jola.
        login(self, 'jola_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']

        # Try to create a templink as Marek to Jola's image.
        self.client.logout()
        login(self, 'marek_data')
        url = reverse('templink-list-create', kwargs={'image_pk': image_pk})
        response = self.client.post(url, {'expires_in': 1000})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)

    def test_enterprise_owner_can_see_templinks(self):
        """
        Check that owner with Enterprise account 
        can see templinks to his images.
        """

        # Upload an image.
        login(self, 'marcin_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']

        # Create two templinks and request a listing.
        url = reverse('templink-list-create', kwargs={'image_pk': image_pk})
        response_tl_one = self.client.post(url, {'expires_in': 1000})
        response_tl_two = self.client.post(url, {'expires_in': 2000})
        response_list = self.client.get(url)

        # Make sure same data of both templinks was listed.
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        self.assertCountEqual(
            response_list.data, 
            [response_tl_one.data, response_tl_two.data]
        )

    def test_enterprise_non_owner_cannot_see_templinks(self):
        """
        Check that non-owner user with Enterprise account 
        cannot see templinks to other user image.
        """

        # Upload an image as Marcin.
        login(self, 'marcin_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']

        # Create two templinks.
        url = reverse('templink-list-create', kwargs={'image_pk': image_pk})
        self.client.post(url, {'expires_in': 1000})
        self.client.post(url, {'expires_in': 2000})

        # Try to get templinks listing as Marek.
        self.client.logout()
        login(self, 'marek_data')
        response_list = self.client.get(url)

        self.assertEqual(response_list.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response_list.data.keys()), 1)

    def test_minimum_templink_lifetime(self):
        """
        Makes sure minimum valid templink 'expires_in' value is 300 (s).
        """

        login(self, 'marcin_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']
        url = reverse('templink-list-create', kwargs={'image_pk': image_pk})

        response = self.client.post(url, {'expires_in': 300})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(url, {'expires_in': 299})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_maximum_templink_lifetime(self):
        """
        Makes sure maximum valid templink 'expires_in' value is 30000 (s).
        """

        login(self, 'marcin_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']
        url = reverse('templink-list-create', kwargs={'image_pk': image_pk})

        response = self.client.post(url, {'expires_in': 30000})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(url, {'expires_in': 30001})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TemporaryImageViewTestCase(APITestCase):
    """
    Tests for TemporaryImageView view.
    """

    @classmethod
    def setUpTestData(cls):
        # Get built-in account tiers.
        cls.basic = AccountTier.objects.get(name='Basic')
        cls.premium = AccountTier.objects.get(name='Premium')
        cls.enterprise = AccountTier.objects.get(name='Enterprise')

        # Create users.
        cls.marcin_data = {
            "username": "Marcin",
            "password": "Tomato789",
            "email": "marcin@example.com",
            "account_tier": cls.enterprise
        }
        cls.jola_data = {
            "username": "Jola",
            "password": "Piekarnik4445",
            "email": "jola@foo.com",
            "account_tier": cls.basic
        }

        cls.marcin = User.objects.create_user(**cls.marcin_data)
        cls.jola = User.objects.create_user(**cls.jola_data)

        # Determine whether django would use timezone. 
        # Neccessary for mocking past datetime.
        cls.use_tz = timezone.utc if settings.USE_TZ else None

    def tearDown(self):
        self.client.logout()
    
    def _create_templink(self, image_pk, expires_in):
        """
        Helper function for creating templink to a given image. 
        Returns templink data. Assumes image owner is logged in.
        """

        url = reverse('templink-list-create', kwargs={'image_pk': image_pk})
        templink_response = self.client.post(url, {'expires_in': expires_in})
        return templink_response.data
    
    def _create_templink_in_the_past(self, image_pk, expires_in, created_sec_ago):
        """
        Helper function. Creates templink to a given image, mocking that it
        happened in the past. Returns templink data. Assumes image owner
        is logged in. Wrapper over _create_templink method.
        """
        @mock.patch(
            'django.utils.timezone.now', 
            lambda: datetime.now(tz=self.use_tz) - timedelta(seconds=created_sec_ago)
        )
        def past_create(image_pk, expires_in):
            return self._create_templink(image_pk, expires_in)

        return past_create(image_pk, expires_in)

    def test_templink_leads_to_source_image(self):
        """
        Verifies byte-to-byte identity of the intial image and FileResponse
        returned by templink.
        """
        
        login(self, 'marcin_data')
        image_file = SAMPLE_JPG

        # Upload image and get templink.
        image_response = upload_image(self, image_file)
        image_pk = image_response.data['pk']
        templink_data = self._create_templink(image_pk, 300)

        # Follow templink and get image from response.
        response = self.client.get(templink_data['link'])
        image = response.streaming_content

        # Assert byte-to-byte identity.
        with open(get_path(image_file), 'rb') as source:
            self.assertEqual(source.read(), b''.join(image))

    def test_anyone_can_use_templink(self):
        """
        Makes sure no authentication is needed to get templink image.
        """

        image_file = SAMPLE_JPG

        # Login, upload image and get templink.
        login(self, 'marcin_data')
        image_response = upload_image(self, image_file)
        image_pk = image_response.data['pk']
        templink_data = self._create_templink(image_pk, 300)

        # Follow templink as anonymous user.
        self.client.logout()
        response = self.client.get(templink_data['link'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_templink_expires(self):
        """
        Makes sure temporary links expire after defined number of seconds.
        """
        # Login and upload image.
        login(self, 'marcin_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']

        # Create templink so that it would expire in 2 seconds.
        templink_data = self._create_templink_in_the_past(
            image_pk, 
            expires_in=300, 
            created_sec_ago=298
        )

        # Assert image can be obtained from templink.
        response = self.client.get(templink_data['link'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert after 2 seconds templink has expired.
        sleep(2)
        response = self.client.get(templink_data['link'])
        self.assertEqual(response.status_code, status.HTTP_410_GONE)

    def test_expired_templink_is_deleted_and_blacklisted(self):
        """
        Makes sure templinks are deleted from DB and tokens are blacklisted
        after expired link is accessed.
        """
        # Login and upload image.
        login(self, 'marcin_data')
        image_response = upload_image(self, SAMPLE_JPG)
        image_pk = image_response.data['pk']

        # Create an expired templink.
        templink_data = self._create_templink_in_the_past(
            image_pk, 
            expires_in=300, 
            created_sec_ago=301
        )

        # Assert templink is in DB (DoesNotExist is not raised).
        templink = TempLink.objects.get(pk=templink_data['pk'])
        
        token = templink.token

        # Access templink and check if it still exists in DB.
        response = self.client.get(templink_data['link'])
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        with self.assertRaises(TempLink.DoesNotExist):
            TempLink.objects.get(pk=templink_data['pk'])

        # Make sure token was blacklisted.
        self.assertTrue(TempLinkTokenBlacklist.objects.get(token=token))
        

def upload_image(inst, image_name):
    """
    Helper function for uploading images from current folder.
    """
    url = reverse('image-list-upload')
    with open(get_path(image_name), 'rb') as img:
        response = inst.client.post(url, {'image': img})
        return response
    
def get_path(filename):
    """ Helper function. Returns path to file from current folder. """
    return path.join(path.dirname(__file__), filename)

def login(inst, user_data):
    """
    Helper function for logging user in and asserting correct login.
    """
    inst.assertTrue(
        inst.client.login(
                username=getattr(inst, user_data)['username'], 
                password=getattr(inst, user_data)['password']
        ),
        'Login failed.'
    )

def get_serializer_readable_fields(serializer):
    """
    Helper function for retrieving non-write-only fields from serializer.
    """
    fields = serializer.Meta.fields
    extra_kwargs = getattr(serializer.Meta, 'extra_kwargs', None)
    if extra_kwargs:
        fields = [
            field for field 
            in fields 
            if not extra_kwargs.get(field, {}).get('write_only', False)
        ]
    return fields
