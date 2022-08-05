from django.urls import path 

from . import views 

app_name = "museum_site"
urlpatterns = [
    path('', views.index, name='index'),
    path('<str:prolific_id>', views.index, name = 'index'),
    path('artwork/<str:artwork_id>/', views.artwork, name='artwork'),
    path('rating/', views.save_rating, name='rating'),
    path('selected/', views.selected_artwork, name = 'selected'),
    path('transition/', views.transition_study_stage, name = 'transition'),
    path('post-study/<str:which_form>/', views.post_study, name='post-study'),
    path('thank-you/', views.thank_you, name='thank-you')
]
