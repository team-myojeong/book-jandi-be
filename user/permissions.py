from rest_framework.permissions import BasePermission


class IsNotSignupComepleted(BasePermission):
    """
    인증됐지만 회원가입을 완료하지 않은 사용자
    """
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False
        
        if user.job:
            return False
        
        return True
