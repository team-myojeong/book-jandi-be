from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from book.models import Book
from book.serializers import BookSerializer
from poll.models import Poll, Vote
from poll.serializers import PollSerializer, VoteSerializer, OpinionSerializer, RecentPollSerializer, PopularPollSerializer
from bookjandi.permissions import IsSignupComepleted


class PollView(APIView):
    def get_permissions(self):
        """
        GET Method 요청인 경우 permission AllowAny
        그 외의 요청은 IsSignupCompleted
        """
        if self.request.method == 'GET':
            return [AllowAny()]
        
        return [IsSignupComepleted()]

    def get(self, request):
        """
        투표글 조회
        """
        id_ = request.GET.get('id')
        if not id_:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        
        try:
            poll_data = (
                Poll.objects
                .select_related(
                    'book',
                    'user__job',
                    'user__career'
                )
                .get(id=id_)
            )
        except Poll.DoesNotExist:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        
        serialized_poll_data = PollSerializer(poll_data, context={'request_user': request.user}).data

        return Response(serialized_poll_data, status.HTTP_200_OK)


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


class VoteView(APIView):
    permission_classes = [IsSignupComepleted]

    def post(self, request):
        """
        투표하기
        내가 작성한 투표글의 경우 투표 불가
        투표글 하나 당 1회 투표 가능
        의견도 한번에 작성 가능
        """
        request_data = request.data.copy()
        user = request.user

        request_data['user'] = user.id
        request_data['poll'] = request_data['id']
        request_data['job'] = user.job.id
        request_data['career'] = user.career.id

        try:
            poll_user_id = Poll.objects.select_related('user').get(id=request_data['poll']).user.id
            if request_data['user'] == poll_user_id:
                return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)

        try:
            Vote.objects.get(poll=request_data['poll'], user=request_data['user'])
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        except Vote.DoesNotExist:
            vote_serializer = VoteSerializer(data=request_data)

            contents = request_data.get('contents')
            if contents:
                opinion_serialiser = OpinionSerializer(data=request_data)
                if not opinion_serialiser.is_valid():
                    return Response({'error': 'error'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

            if not vote_serializer.is_valid():
                return Response({'error': 'error'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            with transaction.atomic():
                vote_serializer.save()
                if contents:
                    opinion_serialiser.save()

        return Response({'success': True}, status.HTTP_200_OK)


class RecentPollView(APIView):
    def get(self, request):
        limit = int(request.GET.get('limit'))
        if not limit:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        last = request.GET.get('last', 0)

        poll_data = (
            Poll.objects
            .select_related('book')
            .prefetch_related('vote_set')
            .filter(id__lt=last)
            .order_by('-created_at')[:limit]
        )
        serialized_poll_data = RecentPollSerializer(poll_data, many=True).data

        return Response({'poll_list': serialized_poll_data}, status.HTTP_200_OK)


class PopularPollView(APIView):
    def get(self, request):
        today = timezone.now()
        start_of_week = (today - timezone.timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = (start_of_week + timezone.timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)

        poll_data = (
            Poll.objects
            .select_related('book')
            .prefetch_related('vote_set', 'opinion_set')
            .annotate(
                vote_count=Count('vote'),
                opinion_count=Count('opinion')
            )
            .filter(created_at__range=[start_of_week, end_of_week])
            .order_by('-vote_count', '-created_at')[:5]
        )
        serialized_poll_data = PopularPollSerializer(poll_data, many=True).data

        return Response({'poll_list': serialized_poll_data}, status.HTTP_200_OK)
