from django.contrib import admin

from user import models


admin.site.register(models.User)
admin.site.register(models.Interest)
admin.site.register(models.Job)
