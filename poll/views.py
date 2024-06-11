from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.db.models import Count, F, Subquery
from django.db.models.query_utils import Q
from django.utils import timezone

from book.models import Book
from book.serializers import BookSerializer
from poll.models import Poll, Vote, Opinion, Bookmark, PollView as PollViewModel
from poll.serializers import PollSerializer, VoteSerializer, OpinionSerializer, PollSimpleSerializer, PopularPollSerializer, BookmarkSerializer, PollViewSerializer
from bookjandi.permissions import IsSignupCompleted


class PollView(APIView):
    def get_permissions(self):
        """
        GET Method 요청인 경우 permission AllowAny
        그 외의 요청은 IsSignupCompleted
        """
        if self.request.method == 'GET':
            return [AllowAny()]
        
        return [IsSignupCompleted()]

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
        
        user = request.user
        if user.is_authenticated and user.job:
            poll_view_data = {
                'career': user.career.id,
                'job': user.job.id,
                'poll': id_
            }
            poll_view_serializer = PollViewSerializer(data=poll_view_data)
            if not poll_view_serializer.is_valid():
                return Response({'error': 'error'}, status=status.HTTP_400_BAD_REQUEST)
            poll_view_serializer.save()

        poll_data.view_count = F('view_count') + 1
        poll_data.save()
        poll_data.refresh_from_db()
        
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

    def delete(self, request):
        """
        투표글 삭제
        투표가 하나라도 되어있으면 삭제 불가
        """
        user = request.user
        poll_id = request.GET.get('id')

        try:
            poll = (
                Poll.objects
                .select_related('user')
                .prefetch_related('vote_set')
                .get(id=poll_id)
            )
        except Poll.DoesNotExist:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        
        poll_user = poll.user
        if user != poll_user:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)

        if poll.vote_set.all():
            return Response({'success': False}, status.HTTP_200_OK)
 
        poll.delete()

        return Response({'success': True}, status.HTTP_200_OK)


class VoteView(APIView):
    permission_classes = [IsSignupCompleted]

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
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.GET.get('limit'))
        if not limit:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        last = request.GET.get('last', 0)

        poll_data = (
            Poll.objects
            .select_related('book')
            .prefetch_related('vote_set')
            .order_by('-created_at')
        )
        poll_data = (poll_data.all() if last == 0 else poll_data.filter(id__lt=last))[:limit]
        serialized_poll_data = PollSimpleSerializer(poll_data, many=True).data

        return Response({'poll_list': serialized_poll_data}, status.HTTP_200_OK)


class PopularPollView(APIView):
    permission_classes = [AllowAny]

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
    

class OpinionView(APIView):
    def get_permissions(self):
        """
        GET Method 요청인 경우 permission AllowAny
        그 외의 요청은 IsSignupCompleted
        """
        if self.request.method == 'GET':
            return [AllowAny()]
        
        return [IsSignupCompleted()]

    def get(self, request):
        """
        의견 조회
        내가 작성한 의견 + 의견 목록
        """
        user = request.user

        poll_id = request.GET.get('id')
        limit = int(request.GET.get('limit', 10))
        last = request.GET.get('last', 0)

        select_related = ('user', 'user__job', 'user__career', 'poll')
        condition = Q(poll=poll_id) if last == 0 else Q(id__lt=last) & Q(poll=poll_id)

        opinion_data = (
            Opinion.objects
            .select_related(*select_related)
            .filter(condition)
            .order_by('-created_at')[:limit]
        )
        serialized_opinion_data = OpinionSerializer(opinion_data, many=True).data

        response = {
            'my_opinion': None,
            'opinion_list': serialized_opinion_data
        }

        if last is None and user.is_authenticated:    # 최초 호출
            try:
                opinion_data = Opinion.objects.select_related(*select_related).get(poll=poll_id, user=user)
            except Opinion.DoesNotExist:
                return Response(response, status.HTTP_200_OK)
            
            response['my_opinion'] = OpinionSerializer(opinion_data).data

        return Response(response, status.HTTP_200_OK)

    def post(self, request):
        """
        의견 작성
        내가 작성한 글의 경우 의견 작성 불가능 -> 투표가 본인이 작성한 글은 불가능하므로 확인 안 해도 됨
        투표한 글만 의견 작성 가능
        의견은 하나만 작성 가능

        poll 존재 여부
            -> 투표가 하나라도 됐다면 삭제 불가능하므로 의견을 작성한다는 것은 투표를 했다는 것이고, 그렇다면 poll이 존재
        """
        user = request.user
        request_data = request.data.copy()

        request_data['user'] = user.id
        request_data['poll'] = request_data['id']

        try:
            vote = Vote.objects.get(poll=request_data['poll'], user=user)
        except Vote.DoesNotExist:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        
        try:
            opinion = Opinion.objects.get(poll=request_data['poll'], user=user)
        except Opinion.DoesNotExist:
            opinion_serialiser = OpinionSerializer(data=request_data)
            if opinion_serialiser.is_valid():
                saved_data = opinion_serialiser.save()
                return Response({'id': saved_data.id}, status.HTTP_200_OK)
            
            return Response({'error': 'error'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        의견 삭제
        내가 작성한 의견만 삭제 가능
        """
        user = request.user
        opinion_id = request.GET.get('id')

        try:
            opinion = Opinion.objects.select_related('user').get(id=opinion_id)
        except Opinion.DoesNotExist:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)

        if user != opinion.user:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        
        opinion.delete()

        return Response({'success': True}, status.HTTP_200_OK)


class BookmarkView(APIView):
    permission_classes = [IsSignupCompleted]

    def post(self, request):
        """
        북마크 하기 및 북마크 취소
        기존에 북마크가 되어있으면 취소, 아니면 추가
        """
        user = request.user
        request_data = request.data.copy()

        poll_id = request_data['id']

        try:
            bookmark = Bookmark.objects.get(user=user, poll=poll_id)
        except Bookmark.DoesNotExist:
            saved_data = {
                'user': user.id,
                'poll': poll_id
            }
            bookmark_serializer = BookmarkSerializer(data=saved_data)
            if bookmark_serializer.is_valid():
                bookmark_serializer.save()

                return Response({'is_bookmark': True}, status.HTTP_200_OK)

            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)

        bookmark.delete()

        return Response({'is_bookmark': False}, status.HTTP_200_OK)
    

class PollResultView(APIView):
    permission_classes = [IsSignupCompleted]

    def get(self, request):
        """
        통계 조회

        * 투표 비율
        * 전체 및 각 잔디 투표 수, 의견들의 각 잔디 수
        * 가장 많이 조회한 직무 / 경력
        * 많이 조회한 3개 직무와 그 직무에서의 경력 비율
        """
        poll_id = request.GET.get('id')

        vote_data = (
            Vote.objects
            .filter(poll=poll_id)
            .values('grass')
            .annotate(count=Count('id'))
            .order_by('grass')
        )
        if not vote_data:
            return Response({}, status=status.HTTP_200_OK)
        
        dried_vote_count = vote_data[0]['count']
        green_vote_count = vote_data[1]['count']
        vote_count = dried_vote_count + green_vote_count

        if vote_count < 5:
            return Response({}, status=status.HTTP_200_OK)

        opinion_count_with_grass_data = (
            Opinion.objects
            .filter(poll=poll_id)
            .values('vote__grass')
            .annotate(count=Count('id'))
            .order_by('vote__grass')
        )

        if opinion_count_with_grass_data:
            dried_opinion_count = opinion_count_with_grass_data[0]['count']
            green_opinion_count = opinion_count_with_grass_data[1]['count']
        else:
            dried_opinion_count = 0
            green_opinion_count = 0
        
        top_data = (
            PollViewModel.objects
            .filter(poll=poll_id)
            .values('job', 'career')
            .annotate(
                count=Count('id'),
                career_simple_text=F('career__simple_text'),
                job_name=F('job__name')
            )
            .order_by('-count')
            .first()
        )
        
        top_3_data = (
            PollViewModel.objects
            .filter(
                poll=poll_id,
                job__in=Subquery(
                    PollViewModel.objects
                    .filter(poll=poll_id)
                    .values('job')
                    .annotate(count=Count('id'))
                    .values('job')[:3]
                )
            )
            .values('career', 'job')
            .annotate(
                count=Count('id'),
                job_name=F('job__name')
            )
        )

        job_name_view_count = {}
        for data in top_3_data:
            job_name = data['job_name']
            if job_name not in job_name_view_count:
                job_name_view_count[job_name] = [0] * 5
            job_name_view_count[job_name][data['job'] - 1] = data['count']

        ranking_detail = []
        job_name_view_count = dict(sorted(job_name_view_count.items(), key=lambda x: sum(x[1])))
        for job_name, view_count_list in job_name_view_count.items():
            total_view_count = sum(view_count_list)
            if total_view_count > 0:
                for idx, view_count in enumerate(view_count_list):
                    view_count_list[idx] = round(view_count / total_view_count * 100)

            ranking_detail.append(
                {
                    'job': job_name,
                    'percentage': view_count_list
                }
            )

        response = {
            'green_percentage': round(green_vote_count / vote_count * 100),
            'dried_percentage': round(dried_vote_count / vote_count * 100),
            'total': {
                'vote_count': vote_count,
                'green_count': green_vote_count,
                'dried_count': dried_vote_count,
                'green_opinion_count': green_opinion_count,
                'dried_opinion_count': dried_opinion_count
            },
            'ranking': {
                'top_career': top_data['career_simple_text'],
                'top_job': top_data['job_name'],
                'detail': ranking_detail
            }
        }

        return Response(response, status=status.HTTP_200_OK)
