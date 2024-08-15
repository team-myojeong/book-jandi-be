from rest_framework.permissions import BasePermission


class IsSignupCompleted(BasePermission):
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


class AllowAnyGetIsSignupCompletedElse(BasePermission):
    """
    GET Method 요청인 경우 AllowAny
    그 외의 요청은 IsSignupCompleted
    """
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        
        user = request.user

        if user.is_authenticated and user.job:
            return True
        
        return False
