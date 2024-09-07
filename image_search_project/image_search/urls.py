from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_similar_products, name='search_similar_products'),
]
