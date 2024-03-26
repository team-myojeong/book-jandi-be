from rest_framework.permissions import BasePermission


class IsSignupComepleted(BasePermission):
    """
    회원가입까지 완료한 사용자
    """
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False
        
        if user.job:
            return True
        
        return False
