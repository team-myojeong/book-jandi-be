import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from user.models import User
from bookjandi.settings import KAKAO_REST_API_KEY, KAKAO_CALLBACK_URI

BASE_URL = 'http://127.0.0.1:8000'


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
