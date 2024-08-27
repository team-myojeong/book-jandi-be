from rest_framework import status
from rest_framework.exceptions import APIException


class RequestValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '요청 파라미터 형식 오류'


class ObjectNotFound(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '존재하지 않는 대상'


class InsertError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '데이터베이스 삽입 오류'


class HasNoPermission(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '권한 없음'
