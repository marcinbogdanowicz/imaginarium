from django.contrib import admin
from .models import User, AccountTier, ThumbnailSize, Image


admin.site.register(User)
admin.site.register(AccountTier)
admin.site.register(ThumbnailSize)
admin.site.register(Image)
