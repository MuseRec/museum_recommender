from django.urls import path 
#from django.conf.urls import url 
from django.urls import include, re_path

from . import views

app_name = "collector"
urlpatterns = [
    path('log/', views.log, name='interaction_logger'),
    path('page/', views.page, name='page_analytics')
]
