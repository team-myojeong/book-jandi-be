from rest_framework import serializers
from rest_framework.serializers import ValidationError

from user.models import User


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
