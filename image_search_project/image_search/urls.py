from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_view, name='search_view'),
    path('results/', views.results_view, name='results'),
    path('', views.home_view, name='home'),
    path('search/', views.search, name='search'),
]