from django.urls import path 

from . import views 

urlpatterns = [
    path('', views.index, name = 'index'),
    path('<str:artwork_id>', views.artwork, name = 'artwork'),
    path('rating/', views.save_rating, name = 'rating')
]
