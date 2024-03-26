from django.urls import path

from poll import views

urlpatterns = [
    path('', views.PollView.as_view()),
]
