from rest_framework import serializers
from rest_framework.serializers import ValidationError

from poll.models import BookMark
from user.models import User, Job, Career


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['job', 'career', 'profile']

    def validate(self, data):
        """
        job, career 필수
        """
        if not data['job']:
            raise ValidationError({'error': 'job 데이터 없음'})
        
        if not data['career']:
            raise ValidationError({'error': 'career 데이터 없음'})
        
        return data
    
    def update(self, instance, validated_data):
        instance.profile = validated_data['job'].default_image
        instance.job = validated_data['job']
        instance.career = validated_data['career']

        instance.save()

        return instance
    

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['job_id', 'job_text']

    job_id = serializers.IntegerField(source='id', read_only=True)
    job_text = serializers.CharField(source='name', read_only=True)


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = ['career_id', 'career_text']

    career_id = serializers.IntegerField(source='id', read_only=True)
    career_text = serializers.CharField(source='long_text', read_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'profile', 'job', 'career']

    name = serializers.CharField(source='nickname', read_only=True)
    job = serializers.CharField(source='job.name', read_only=True)
    career = serializers.CharField(source='career.simple_text', read_only=True)


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookMark
        fields = [
            'id',
            'poll_id', 'cover', 'title', 'writer_id', 'writer_name', 'question', 'description',
            'view_count', 'vote_count', 'opinion_count',
            'vote', 'is_opinion'
        ]

    poll_id = serializers.IntegerField(source='poll.id', read_only=True)
    cover = serializers.URLField(source='poll.book.cover', read_only=True)
    title = serializers.CharField(source='poll.book.title', read_only=True)
    writer_id = serializers.IntegerField(source='poll.user.id', read_only=True)
    writer_name = serializers.CharField(source='poll.user.nickname', read_only=True)
    question = serializers.CharField(source='poll.question', read_only=True)
    description = serializers.CharField(source='poll.description', read_only=True)

    vote = serializers.SerializerMethodField(read_only=True)
    def get_vote(self, obj):
        request_user = self.context.get('request_user')
        if not request_user.is_authenticated:
            return 'none'

        user_votes = obj.poll.user_votes
        return user_votes[0].grass if user_votes else 'none'

    is_opinion = serializers.SerializerMethodField(read_only=True)
    def get_is_opinion(self, obj):
        return obj.is_opinion
    
    view_count = serializers.SerializerMethodField(read_only=True)
    def get_view_count(self, obj):
        return 0    # TODO 조회수 추후 개발
    
    vote_count = serializers.SerializerMethodField(read_only=True)
    def get_vote_count(self, obj):
        return obj.vote_count
    
    opinion_count = serializers.SerializerMethodField(read_only=True)
    def get_opinion_count(self, obj):
        return obj.opinion_count
