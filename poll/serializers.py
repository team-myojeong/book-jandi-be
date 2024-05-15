from rest_framework import serializers
from rest_framework.serializers import ValidationError

from user.models import User
from poll.models import Poll, Vote, Opinion, BookMark


class PollWriterInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'profile', 'job', 'career']

    name = serializers.CharField(source='nickname', read_only=True)
    job = serializers.CharField(source='job.name', read_only=True)
    career = serializers.CharField(source='career.simple_text', read_only=True)


class PollBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['cover', 'title', 'author_list', 'translator_list', 'publisher']

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


class PollSerializer(PollBookSerializer):
    class Meta:
        model = Poll
        fields = [
            'question', 'description', 'user', 'book',
            'difficulty_level', 'writer_info', 'cover', 'title', 'publisher',
            'author_list', 'translator_list', 'is_mine', 'vote'
        ]
        extra_kwargs = {
            'user': {'write_only': True},
            'book': {'write_only': True}
        }

    difficulty_level = serializers.IntegerField(source='level')
    writer_info = PollWriterInfoSerializer(source='user', read_only=True)

    is_mine = serializers.SerializerMethodField(read_only=True)
    def get_is_mine(self, obj):
        request_user = self.context.get('request_user')
        
        if not request_user.is_authenticated:
            return False
        
        if not request_user.job:
            return False
        
        return obj.user == request_user
    
    vote = serializers.SerializerMethodField(read_only=True)
    def get_vote(self, obj):
        request_user = self.context.get('request_user')
        poll_id = obj.id

        if not request_user.is_authenticated or not request_user.job:
            return 'none'

        try:
            grass = obj.vote_set.get(poll=poll_id, user=request_user).grass
        except Vote.DoesNotExist:
            return 'none'
        
        return grass


    def validate_difficulty_level(self, value):
        if not (1 <= value <= 3):
            raise ValidationError({'error': 'invalid data'})

        return value
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        writer_info = data.pop('writer_info')
        is_mine = data.pop('is_mine')
        vote = data.pop('vote')
        representation_data = {
            'poll': data,
            'writer_info': writer_info,
            'is_mine': is_mine,
            'vote': vote,
            'is_bookmark': False    # TODO
        }

        return representation_data


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['user', 'poll', 'job', 'career', 'grass']


class OpinionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opinion
        fields = [
            'id', 'user', 'poll', 'contents', 'created_at',
            'writer_info'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'user': {'write_only': True},
            'poll': {'write_only': True}
        }

    created_at = serializers.DateTimeField(format="%Y.%m.%d", read_only=True)
    writer_info = PollWriterInfoSerializer(source='user', read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        writer_info = data.pop('writer_info')
        data['writer_id'] = writer_info.pop('id')
        data.update(writer_info)

        return data


class PollSimpleSerializer(PollBookSerializer):
    class Meta:
        model = Poll
        fields = [
            'poll_id',
            'cover', 'title', 'author_list', 'translator_list', 'publisher',
            'vote_percentage', 'view_count'
        ]

    poll_id = serializers.IntegerField(source='id', read_only=True)

    vote_percentage = serializers.SerializerMethodField(read_only=True)
    def get_vote_percentage(self, obj):
        vote_count = obj.vote_set.count()
        if vote_count >= 5:
            green_count = obj.vote_set.filter(grass='green').count()
            return round(green_count / vote_count * 100)

        return -1
    
    view_count = serializers.SerializerMethodField(read_only=True)
    def get_view_count(self, obj):
        return 0    # TODO 조회수 추후 개발


class PopularPollSerializer(PollSimpleSerializer):
    class Meta:
        model = Poll
        fields = [
            'poll_id',
            'cover', 'title', 'author_list', 'translator_list', 'publisher',
            'vote_percentage', 'view_count'
        ]


class UserPollSerializer(PopularPollSerializer):
    class Meta:
        model = Poll
        fields = [
            'poll_id',
            'cover', 'title',
            'writer_id', 'writer_name', 'question', 'description',
            'view_count', 'vote_count', 'opinion_count'
        ]

    writer_id = serializers.IntegerField(source='user.id', read_only=True)
    writer_name = serializers.CharField(source='user.nickname', read_only=True)
    
    vote_count = serializers.SerializerMethodField(read_only=True)
    def get_vote_count(self, obj):
        return obj.vote_count
    
    opinion_count = serializers.SerializerMethodField(read_only=True)
    def get_opinion_count(self, obj):
        return obj.opinion_count


class UserVotePollSerializer(UserPollSerializer):
    class Meta:
        model = Poll
        fields = [
            'poll_id',
            'cover', 'title',
            'writer_id', 'writer_name', 'question', 'description',
            'view_count', 'vote_count', 'opinion_count',
            'vote', 'is_opinion', 'opinion_contents'
        ]

    vote = serializers.SerializerMethodField(read_only=True)
    def get_vote(self, obj):
        request_user = self.context.get('request_user')
        poll_id = obj.id

        if not request_user.is_authenticated:
            return 'none'

        try:
            grass = obj.vote_set.get(poll=poll_id, user=request_user).grass
        except Vote.DoesNotExist:
            return 'none'
        
        return grass

    opinion = None
    is_opinion = serializers.SerializerMethodField(read_only=True)
    def get_is_opinion(self, obj):
        request_user = self.context.get('request_user')
        poll_id = obj.id
        
        if not request_user.is_authenticated:
            return False
        
        try:
            opinion = obj.opinion_set.get(poll=poll_id, user=request_user)
        except Opinion.DoesNotExist:
            return False
        
        self.opinion = opinion
        return True
    
    opinion_contents = serializers.SerializerMethodField(read_only=True)
    def get_opinion_contents(self, obj):
        return self.opinion.contents if self.opinion else None


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookMark
        fields = ['user', 'poll']
