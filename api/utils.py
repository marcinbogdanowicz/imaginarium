from secrets import token_urlsafe
from . import models

def file_name_generator(instance, filename):
    """
    Appends a 12 bit random string prefix to file name.
    """
    prefix = token_urlsafe(nbytes=12)
    return f"{prefix}{filename}"


def generate_token():
    """
    Generates a 32 bit random token using secrets.token_urlsafe.
    Makes sure token is neither active nor blacklisted.
    """

    while True:
        token = token_urlsafe(nbytes=32)
        token_is_active = bool(models.TempLink.objects.filter(token=token))
        token_is_blacklisted = bool(
            models.TempLinkTokenBlacklist.objects.filter(token=token)
        )

        if not token_is_active and not token_is_blacklisted:
            return token
