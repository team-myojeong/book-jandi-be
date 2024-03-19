from rest_framework import serializers
from rest_framework.serializers import ValidationError

from user.models import User


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['job', 'career', 'interest1', 'interest2', 'interest3']

    def validate(self, data):
        """
        job, career 필수
        interest 최소 하나 필수, 중복 시 에러 처리
        """
        if not data['job']:
            raise ValidationError({'error': 'job 데이터 없음'})
        
        if not data['career']:
            raise ValidationError({'error': 'career 데이터 없음'})
        
        interest_list = list(filter(lambda x: x is not None, [data['interest1'], data['interest2'], data['interest3']]))
        if not any(interest_list):
            raise ValidationError({'error': 'interest 데이터 없음'})
        if len(set(interest_list)) != len(interest_list):
            raise ValidationError({'error': 'interest 데이터 중복'})
        
        return data
