from rest_framework import serializers
from rest_framework.serializers import ValidationError

from user.models import User
from poll.models import Poll, Vote, Opinion


class PollWriterInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'profile', 'job', 'career']

    name = serializers.CharField(source='nickname', read_only=True)
    job = serializers.CharField(source='job.name', read_only=True)
    career = serializers.CharField(source='career.simple_text', read_only=True)


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = [
            'question', 'description', 'user', 'book',
            'difficulty_level', 'writer_info', 'cover', 'title', 'publisher',
            'author_list', 'translator_list', 'is_mine'
        ]
        extra_kwargs = {
            'user': {'write_only': True},
            'book': {'write_only': True}
        }

    difficulty_level = serializers.IntegerField(source='level')
    writer_info = PollWriterInfoSerializer(source='user', read_only=True)
    cover = serializers.URLField(source='book.cover', read_only=True)
    title = serializers.CharField(source='book.title', read_only=True)
    publisher = serializers.CharField(source='book.publisher', read_only=True)

    author_list = serializers.SerializerMethodField(read_only=True)
    def get_author_list(self, obj):
        author_list = [author for author in obj.book.author.split(',') if author]
        return author_list
    
    translator_list = serializers.SerializerMethodField(read_only=True)
    def get_translator_list(self, obj):
        translators = obj.book.translator
        if not translators:
            return None
        
        translator_list = [translator for translator in obj.book.translator.split(',') if translator]
        return translator_list
    
    is_mine = serializers.SerializerMethodField(read_only=True)
    def get_is_mine(self, obj):
        request_user = self.context.get('request_user')
        
        if not request_user.is_authenticated:
            return False
        
        if not request_user.job:
            return False
        
        return obj.user == request_user

    def validate_difficulty_level(self, value):
        if not (1 <= value <= 3):
            raise ValidationError({'error': 'invalid data'})

        return value
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        writer_info = data.pop('writer_info')
        is_mine = data.pop('is_mine')
        representation_data = {
            'poll': data,
            'writer_info': writer_info,
            'is_mine': is_mine,
            'vote': 'none', # TODO
            'is_bookmark': False    # TODO
        }

        return representation_data


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['user', 'poll', 'grass']


class OpinionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opinion
        fields = ['user', 'poll', 'contents']
