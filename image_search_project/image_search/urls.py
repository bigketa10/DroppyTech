from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_view, name='search_view'),
]

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('image_search/', include('image_search.urls')),
]