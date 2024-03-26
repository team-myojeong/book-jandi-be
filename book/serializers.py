from rest_framework import serializers

from book.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'isbn', 'title', 'author', 'publisher', 'translator', 'cover', 'poll_count',
            'author_list', 'translator_list'
        ]

        extra_kwargs = {
            'author': {'write_only': True},
            'translator': {'write_only': True}
        }

    poll_count = serializers.SerializerMethodField()
    def get_poll_count(self, obj):
        return 0
    
    author_list = serializers.SerializerMethodField(read_only=True)
    def get_author_list(self, obj):
        return obj.author.split(',')
    
    translator_list = serializers.SerializerMethodField(read_only=True)
    def get_translator_list(self, obj):
        return obj.translator.split(',')
