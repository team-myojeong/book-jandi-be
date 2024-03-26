from django.urls import path

from book import views

urlpatterns = [
    path('', views.BookView.as_view()),
    path('search/', views.BookSearchView.as_view()),
]
