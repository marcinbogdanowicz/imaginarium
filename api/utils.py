from secrets import token_urlsafe as token


def file_name_generator(instance, filename):
    """
    Appends a 12 bit random string prefix to file name.
    """
    prefix = token(nbytes=12)
    return f"{prefix}{filename}"