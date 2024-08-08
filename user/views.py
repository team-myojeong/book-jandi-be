import requests
from django.db.models.query_utils import Q
from django.db.models import Count, Exists, OuterRef, Prefetch
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from bookjandi.permissions import IsSignupCompleted
from poll.models import Poll, Bookmark, Opinion, Vote, PollView as PollViewModel
from poll.serializers import UserPollSerializer, UserVotePollSerializer
from user.models import User, Job, Career
from user.serializers import SignupSerializer, JobSerializer, CareerSerializer, UserSerializer, BookmarkSerializer
from user.permissions import IsNotSignupComepleted
from bookjandi.statics import KAKAO_REST_API_KEY, KAKAO_CALLBACK_URI, BASE_URL


class UserAuthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')
        token = self._get_token(code)
        email = self._get_email(token)

        response = self._sign_in(email, token, code)

        return response

    def _get_token(self, code: str):
        params = {
            'grant_type': 'authorization_code',
            'client_id': KAKAO_REST_API_KEY,
            'redirect_uri': KAKAO_CALLBACK_URI,
            'code': code
        }
        toekn_request = requests.get(f'https://kauth.kakao.com/oauth/token', params=params)
        toekn_request_json = toekn_request.json()
        if toekn_request.status_code != 200:
            return Response(toekn_request_json, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        access_token = toekn_request_json.get('access_token')

        return access_token
    
    def _get_email(self, access_token: str):
        profile_request = requests.get('https://kapi.kakao.com/v2/user/me', headers={'Authorization': f'Bearer {access_token}'})
        profile_request_json = profile_request.json()
        if profile_request.status_code != 200:
            return Response(profile_request_json, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        kakao_account = profile_request_json.get('kakao_account')
        email = kakao_account.get('email')

        return email
    
    def _sign_in(self, email: str, access_token: str, code: str):
        try:
            user = User.objects.get(email=email)
            response = self._get_sign_in_response(access_token, code, bool(user.job))

            return response
        except User.DoesNotExist:
            response = self._get_sign_in_response(access_token, code, False)

            return response
        
    def _get_sign_in_response(self, access_token: str, code: str, signup_complete: bool):
        data = {
            'access_token': access_token,
            'code': code
        }
        accept = requests.post(f'{BASE_URL}/user/login/finish/', data=data)
        if (accept_status := accept.status_code) != 200:
            return Response({'message': f"failed to {'signin' if signup_complete else 'signup'}"}, status=accept_status)
        accept_json = accept.json()

        refresh_token = accept.headers['Set-Cookie'].split('refresh_token=')[-1].split(';')[0]

        COOKIE_MAX_AGE = 3600 * 24 * 14 # 14 days

        response = {
            'access_token': accept_json['access'],
            'signup_complete': signup_complete
        }
        response_with_cookie = Response(response)
        response_with_cookie.set_cookie(
            'refresh_token',
            refresh_token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite='Lax'
        )

        return response_with_cookie


class KakaoLoginView(SocialLoginView):
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = KAKAO_CALLBACK_URI


class SignupView(APIView):
    permission_classes = [IsNotSignupComepleted]

    def post(self, request):
        """
        유저 정보 업데이트
        job, career, interest 데이터 추가
        """
        user = User.objects.get(id=request.user.id)
        
        request_data = request.data.copy()
        request_data['job'] = request_data['job_id']
        request_data['career'] = request_data['career_id']
        
        signup_serializer = SignupSerializer(user, data=request_data, partial=True)

        if signup_serializer.is_valid():
            signup_serializer.save()
            
            return Response({'success': True}, status.HTTP_200_OK)
        
        return Response({'success': False}, status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class JobView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        직무 조회
        """
        job_data = Job.objects.all()
        serialized_job_data = JobSerializer(job_data, many=True).data

        return Response({'job_list': serialized_job_data}, status.HTTP_200_OK)


class CareerView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        연차 조회
        """
        career_data = Career.objects.all()
        serialized_career_data = CareerSerializer(career_data, many=True).data

        return Response({'career_list': serialized_career_data}, status.HTTP_200_OK)


class PollView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        특정 유저가 작성한 투표글 조회
        """
        user_id = request.GET.get('id')
        limit = int(request.GET.get('limit', 10))
        last = int(request.GET.get('last', 0))

        select_related = ('user', 'user__job', 'user__career', 'book')
        condition = Q(user=user_id) if last == 0 else Q(id__lt=last) & Q(user=user_id)

        poll_data = (
            Poll.objects
            .select_related(*select_related)
            .annotate(
                vote_count=Count('vote', distinct=True),
                opinion_count=Count('opinion', distinct=True)
            )
            .filter(condition)
            .order_by('-created_at')[:limit]
        )
        serialized_poll_data = UserPollSerializer(poll_data, many=True).data

        poll_count = Poll.objects.filter(user=user_id).count()
        response = {
            'count': poll_count,
            'poll_list': serialized_poll_data
        }

        return Response(response, status.HTTP_200_OK)


class VotePollView(APIView):
    permission_classes = [AllowAny]

    def get(selt, request):
        """
        특정 유저가 투표한 투표글 조회
        """
        user_id = request.GET.get('id')
        limit = int(request.GET.get('limit', 10))
        last = int(request.GET.get('last', 0))

        condition = Q(vote__user=user_id) if last == 0 else Q(id__lt=last) & Q(vote__user=user_id)
        poll_data = (
            Poll.objects
            .select_related(
                'user',
                'book'
            )
            .annotate(
                vote_count=Count('vote', distinct=True),
                opinion_count=Count('opinion',distinct=True)
            )
            .filter(condition)
            .order_by('-created_at')[:limit]
        )

        serialized_poll_data = UserVotePollSerializer(poll_data, context={'request_user': request.user}, many=True).data

        poll_count = Poll.objects.filter(vote__user=user_id).count()
        response = {
            'count': poll_count,
            'poll_list': serialized_poll_data
        }

        return Response(response, status.HTTP_200_OK)
    

class UserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = int(request.GET.get('id'))

        try:
            user_data = User.objects.select_related('job', 'career').get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'error'}, status.HTTP_400_BAD_REQUEST)
        
        serialized_user_data = UserSerializer(user_data).data

        return Response(serialized_user_data, status.HTTP_200_OK)


class BookmarkView(APIView):
    permission_classes = [IsSignupCompleted]

    def get(self, request):
        """
        특정 유저의 북마크 목록 조회
        """
        user = request.user
        limit = int(request.GET.get('limit', 10))
        last = int(request.GET.get('last', 0))

        condition = Q(user=user) if last == 0 else Q(id__lt=last) & Q(user=user)

        book_data = (
            Bookmark.objects
            .select_related(
                'user',
                'poll',
                'poll__user',
                'poll__book'
            )
            .prefetch_related(
                Prefetch('poll__vote_set', queryset=Vote.objects.filter(user=user), to_attr='user_votes')
            )
            .filter(condition)
            .annotate(
                vote_count=Count('poll__vote', distinct=True),
                opinion_count=Count('poll__opinion', distinct=True),
                is_opinion=Exists(Opinion.objects.filter(poll=OuterRef('poll'), user=user)),
                view_count=Count('poll__pollview', distinct=True)
            )
            .order_by('-created_at')[:limit]
        )

        serialized_book_data = BookmarkSerializer(book_data, context={'request_user': user}, many=True).data

        bookmark_count = Bookmark.objects.filter(user=user).count()
        response = {
            'count': bookmark_count,
            'bookmark_list': serialized_book_data
        }

        return Response(response, status.HTTP_200_OK)
