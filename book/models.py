from django.db import models


class Book(models.Model):
    isbn = models.CharField(unique=True, max_length=13)
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=50)
    publisher = models.CharField(max_length=20)
    translator = models.CharField(null=True, max_length=50)
    cover = models.URLField()

    def __str__(self):
        return self.title
