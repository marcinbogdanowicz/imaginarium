from django.contrib import admin
from .models import (
    User, 
    AccountTier, 
    ThumbnailSize, 
    Image, 
    TempLink, 
    TempLinkTokenBlacklist
)


admin.site.register(User)
admin.site.register(AccountTier)
admin.site.register(ThumbnailSize)
admin.site.register(Image)
admin.site.register(TempLink)
admin.site.register(TempLinkTokenBlacklist)
