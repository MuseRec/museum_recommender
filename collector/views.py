from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone

from museum_site.views import index
from museum_site.models import User
from .models import Interaction

@ensure_csrf_cookie
def log(request):
    if request.method == 'POST':        
        interaction_event = Interaction(
            user = User.objects.get(user_id = request.session['user_id']),
            timestamp = timezone.now(),
            content_id = request.POST['content_id'],
            event = request.POST['event_type'],
            page = request.POST['page_id']
        )
        print(interaction_event)
        interaction_event.save()

        if request.POST['event_type'] == 'home-button':
            return redirect('index')
        else:
            return HttpResponse('ok')
    else:
        return HttpResponse('log only works with POST')

@ensure_csrf_cookie
def page(request):
    if request.method == 'POST':
        hidden_time = request.POST['hiddenTime']
        dwell_time = request.POST['dwellTime']
        dwell_minus_hidden = request.POST['dwellMinusHidden']
        print(f"Hidden Time: {hidden_time}, Dwell Time: {dwell_time}, Dwell - Hidden: {dwell_minus_hidden}")
        return HttpResponse('ok')