from django.urls import path

from poll import views

urlpatterns = [
    path('', views.PollView.as_view()),
    path('vote/', views.VoteView.as_view()),
    path('recent/', views.RecentPollView.as_view()),
    path('popular/', views.PopularPollView.as_view()),
    path('opinion/', views.OpinionView.as_view()),
    path('bookmark/', views.BookmarkView.as_view()),
    path('vote/detail/', views.PollResultView.as_view()),
]
