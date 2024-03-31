from rest_framework import serializers
from rest_framework.serializers import ValidationError

from poll.models import Poll


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['level', 'question', 'description', 'user', 'book']

    def validate(self, data):
        if not (1 <= data.get('level', 0) <= 3):
            raise ValidationError({'error': 'invalid data'})

        return data
    