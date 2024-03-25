from django.urls import path

from book import views

urlpatterns = [
    path('search/', views.BookSearchView.as_view()),
]
