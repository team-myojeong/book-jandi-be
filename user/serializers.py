from rest_framework import serializers
from rest_framework.serializers import ValidationError

from user.models import User, Job, Career


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['job', 'career']

    def validate(self, data):
        """
        job, career 필수
        """
        if not data['job']:
            raise ValidationError({'error': 'job 데이터 없음'})
        
        if not data['career']:
            raise ValidationError({'error': 'career 데이터 없음'})
        
        return data
    

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
