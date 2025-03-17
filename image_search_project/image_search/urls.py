from django.urls import path
from . import views

urlpatterns = [
    
    path('search/<path:url>/', views.url_search, name='url_search'),

    # Route for the search page
    path('search/', views.search_view, name='search'),

    # Route for displaying search results
    path('results/', views.results_view, name='results'),

    # Home page route
    path('', views.home_view, name='home'),
]