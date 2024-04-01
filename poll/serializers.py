from rest_framework import serializers
from rest_framework.serializers import ValidationError

from poll.models import Poll


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['question', 'description', 'user', 'book', 'difficulty_level']

    difficulty_level = serializers.IntegerField(source='level')

    def validate_difficulty_level(self, value):
        if not (1 <= value <= 3):
            raise ValidationError({'error': 'invalid data'})

        return value
    