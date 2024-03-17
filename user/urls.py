from django.urls import path

from user import views

urlpatterns = [
    path('login/', views.UserAuthView.as_view()),
    path('login/finish/', views.KakaoLoginView.as_view()),
]