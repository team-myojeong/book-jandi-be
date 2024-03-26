from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from book.models import Book
from poll.serializers import PollSerializer
from bookjandi.permissions import IsSignupComepleted


class PollView(APIView):
    permission_classes = [IsSignupComepleted]

    def post(self, request):
        """
        투표글 작성
        """
        request_data = request.data.copy()
        request_data['level'] = request_data.get('difficulty_level')
        request_data['user'] = request.user.id
        try:
            request_data['book'] = Book.objects.get(isbn=request_data.get('isbn')).id
        except Book.DoesNotExist:
            return Response({'error': 'no data'}, status.HTTP_400_BAD_REQUEST)
        
        poll_serializer = PollSerializer(data=request_data)

        if poll_serializer.is_valid():
            saved_data = poll_serializer.save()
            return Response({'id': saved_data.id}, status.HTTP_200_OK)
        
        return Response({'error': 'error'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
