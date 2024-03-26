import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from book.models import Book
from book.serializers import BookSerializer
from book.schemas import BookList
from book.statics import KAKAO_BOOK_SEARCH_URL, KAKAO_BOOK_SEARCH_HEADER, KAKAO_BOOK_SEARCH_SIZE


class BookView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        isbn = request.GET.get('isbn')
        if not isbn or (len(isbn) != 10 and len(isbn) != 13):
            return Response({'message': 'validation error'}, status.HTTP_400_BAD_REQUEST)
        
        try:
            book = Book.objects.get(isbn=isbn)
        except Book.DoesNotExist:
            params = {
                'query': isbn,
                'size': 1,
                'target': 'isbn'
            }
            response = requests.get(KAKAO_BOOK_SEARCH_URL, params=params, headers=KAKAO_BOOK_SEARCH_HEADER)
            if response.status_code != 200:
                return Response({'message': 'kakao api error'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            book_document_list = response.json()['documents']
            if not book_document_list:
                return Response({'message': 'no data'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            book_data = book_document_list[0]
            isbn = book_data['isbn']
            isbn_list = isbn.split(' ')
            if len(isbn_list) == 2:
                isbn = isbn_list[0] if len(isbn_list[0]) == 13 else isbn_list[1]
            author = ','.join(book_data['authors'])
            title = book_data['title']
            publisher = book_data['publisher']
            translator = ','.join(book_data['translators'])
            cover = book_data['thumbnail']

            book = Book(
                isbn=isbn,
                title=title,
                author=author,
                publisher=publisher,
                translator=translator,
                cover=cover
            )

        serializered_book_data = BookSerializer(book).data
        
        return Response(serializered_book_data, status.HTTP_200_OK)


class BookSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
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

        book_list = [
            BookList(
                poll_count=0,   # 추후 수정
                **document
            ).__dict__ for document in book_document_list
        ]

        return Response({'book_list': book_list}, status.HTTP_200_OK)
