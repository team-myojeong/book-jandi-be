from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.db import transaction


class KakaoAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        with transaction.atomic():
            user = super().save_user(request, sociallogin, form)

            oauth_data = sociallogin.account.extra_data
            kakao_profile = oauth_data['kakao_account']['profile']
            user.nickname = kakao_profile['nickname']
            user.profile = kakao_profile['profile_image_url']

            user.save()

        return user