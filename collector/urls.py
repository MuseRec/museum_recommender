from django.urls import path 
from django.conf.urls import url 

from . import views

urlpatterns = [
    path('log/', views.log, name = 'interaction_logger'),
    path('page/', views.page, name = 'page_analytics')
]
