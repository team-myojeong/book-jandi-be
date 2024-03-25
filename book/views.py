import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from book.schemas import BookList
from book.statics import KAKAO_BOOK_SEARCH_URL, KAKAO_BOOK_SEARCH_HEADER, KAKAO_BOOK_SEARCH_SIZE


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
