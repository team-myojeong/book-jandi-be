from django.db import models


class Poll(models.Model):
    level = models.IntegerField()
    question = models.CharField(max_length=100)
    description = models.CharField(null=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey('user.User', on_delete=models.DO_NOTHING)
    book = models.ForeignKey('book.Book', on_delete=models.DO_NOTHING)
