from bookjandi.settings import secrets

BASE_URL = secrets['BASE_URL']

kakao_secrets = secrets['KAKAO']
KAKAO_REST_API_KEY = kakao_secrets['REST_API_KEY']
KAKAO_CALLBACK_URI = kakao_secrets['CALLBACK_URI']

aws_secrets = secrets['AWS']
AWS_ACCESS_KEY = aws_secrets['ACCESS_KEY']
AWS_SECRET_KEY = aws_secrets['SECRET_KEY']
AWS_BUCKET_NAME = aws_secrets['BUCKET_NAME']
AWS_S3_URL = f'https://{AWS_BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/'
