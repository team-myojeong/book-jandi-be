from django.urls import path

from poll import views

urlpatterns = [
    path('', views.PollView.as_view()),
    path('vote/', views.VoteView.as_view()),
    path('recent/', views.RecentPollView.as_view()),
]
