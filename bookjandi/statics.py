from bookjandi.settings import secrets

BASE_URL = secrets['BASE_URL']

kakao_secrets = secrets['KAKAO']
KAKAO_REST_API_KEY = kakao_secrets['REST_API_KEY']
KAKAO_CALLBACK_URI = BASE_URL + '/user/login/'
