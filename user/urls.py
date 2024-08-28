from django.urls import path

from user import views

urlpatterns = [
    path('login/', views.UserAuthView.as_view()),
    path('login/finish/', views.KakaoLoginView.as_view()),
    path('signup/', views.SignupView.as_view()),

    path('job/', views.JobView.as_view()),
    path('career/', views.CareerView.as_view()),
    path('poll/list/', views.PollView.as_view()),
    path('vote/list/', views.VotePollView.as_view()),
    path('', views.UserView.as_view()),
    path('bookmark/list/', views.BookmarkView.as_view()),

    path('test/login/', views.login_test)
]