from django.urls import path 

from . import views 

app_name = "museum_site"
urlpatterns = [
    path('', views.index, name='index'),
    path('artwork/<str:artwork_id>/', views.artwork, name='artwork'),
    path('rating/', views.save_rating, name='rating'),
]
