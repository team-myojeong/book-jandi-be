import requests
from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from poll.models import Poll
from book.schemas import BookList
from book.statics import KAKAO_BOOK_SEARCH_URL, KAKAO_BOOK_SEARCH_HEADER, KAKAO_BOOK_SEARCH_SIZE


class BookSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        도서 검색
        카카오 API 이용
        """
        keyword = request.GET.get('keyword')
        if not keyword:
            return Response({'message': 'validation error'}, status.HTTP_400_BAD_REQUEST)
        
        params = {
            'query': keyword,
            'size': KAKAO_BOOK_SEARCH_SIZE
        }
        response = requests.get(KAKAO_BOOK_SEARCH_URL, params=params, headers=KAKAO_BOOK_SEARCH_HEADER)
        if response.status_code != 200:
            return Response({'message': 'kakao api error'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        book_document_list = response.json()['documents']

        book_isbn_list = []
        for book in book_document_list:
            isbn_list = book['isbn'].split(' ')
            if isbn_list[0]:
                book['isbn'] = isbn_list[0] if len(isbn_list[0]) == 13 else isbn_list[1]

            book_isbn_list.append(book['isbn'])
        
        poll_data_list = (
            Poll.objects
            .select_related('book')
            .filter(book__isbn__in=book_isbn_list)
            .values('book__isbn')
            .annotate(count=Count('*'))
        )
        poll_count = {p['book__isbn']: p['count'] for p in poll_data_list}

        book_list = [
            BookList(
                poll_count=poll_count.get(document['isbn'], 0),
                **document
            ).__dict__ for document in book_document_list
        ]

        return Response({'book_list': book_list}, status.HTTP_200_OK)
