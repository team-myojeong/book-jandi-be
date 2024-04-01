from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from book.models import Book
from book.serializers import BookSerializer
from poll.serializers import PollSerializer
from bookjandi.permissions import IsSignupComepleted


class PollView(APIView):
    permission_classes = [IsSignupComepleted]

    def post(self, request):
        """
        투표글 작성
        DB에 존재하지 않는 책일 경우 request로 받은 책 데이터 저장
        """
        request_data = request.data.copy()
        request_data['user'] = request.user.id
        try:
            book_data = request_data['book']
            request_data['book'] = Book.objects.get(isbn=book_data['isbn']).id
        except Book.DoesNotExist:
            book_data['author'] = ','.join(book_data['author_list'])
            book_data['translator'] = ','.join(book_data['translator_list']) if book_data['translator_list'] else None

            book_serializer = BookSerializer(data=book_data)
            if book_serializer.is_valid():
                save_book = book_serializer.save()
                request_data['book'] = save_book.id
            else:
                return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        
        poll_serializer = PollSerializer(data=request_data)

        if poll_serializer.is_valid():
            saved_data = poll_serializer.save()
            return Response({'id': saved_data.id}, status.HTTP_200_OK)
        
        return Response({'error': 'error'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
