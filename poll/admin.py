from django.contrib import admin

from poll import models


admin.site.register(models.Poll)
admin.site.register(models.Vote)
admin.site.register(models.Opinion)
admin.site.register(models.Bookmark)
admin.site.register(models.PollView)
