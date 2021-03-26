from django.http.response import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

import uuid

from .forms import UserForm, UserDemographicForm
from .models import User, UserDemographic, Artwork, ArtworkVisited

def index(request):
    if request.method == 'POST':
        if 'information_sheet_form' in request.POST:
            return handle_information_sheet_post(request)
        elif 'demographic_form' in request.POST:
            # check that the user has provided consent in the prior step before
            # progressing with collecting their data
            if User.objects.get(user_id = request.session['user_id']).consent:
                return handle_demographic_post(request)
            else:
                # if they haven't, then reload the page with the consent form
                return render(request, 'museum_site/index.html', {
                    'provided_consent': False, 'consent_form': UserForm(),
                    'consent_required_before_demographic': True
                })
    else:
        if 'user_id' in request.session:
            return handle_render_home_page(request)
            
        
        consent_form = UserForm()
        return render(request, 'museum_site/index.html', {
            'provided_consent': False, 'consent_form': consent_form,
        })

def handle_information_sheet_post(request):
    consent_form = UserForm(request.POST)
    if consent_form.is_valid():
        new_user = consent_form.save(commit = False)

        cleaned_data = consent_form.clean()

        # generate the user_id 
        new_user.user_id = str(uuid.uuid4())
        if not "user_id" in request.session: 
            request.session['user_id'] = new_user.user_id

        # if they want to be contacted about the outcome
        if cleaned_data['contact_outcome']:
            new_user.email = cleaned_data['email']
            new_user.contact_outcome = True
        
        new_user.user_created = timezone.now()
        new_user.save()

        # now load the demographic survey
        demographic_form = UserDemographicForm()

        return render(request, 'museum_site/index.html', {
            'provided_consent': True, 'demographic_form': demographic_form,
            'load_demographic': True
        })

def handle_demographic_post(request):
    demographic_form = UserDemographicForm(request.POST)
    if demographic_form.is_valid():
        new_demo = demographic_form.save(commit = False)
        cleaned_data = demographic_form.clean()

        # overall kill, but just to make it clearer...
        new_demo.user = User.objects.get(user_id = request.session['user_id'])
        new_demo.age = cleaned_data['age']
        new_demo.gender = cleaned_data['gender']
        new_demo.education = cleaned_data['education']
        new_demo.work = cleaned_data['work']
        new_demo.submission_timestamp = timezone.now()
        
        new_demo.save()

        # return render(request, 'museum_site/index.html', {
        #     'provided_consent': True, 'page_id': 'index'
        # })
        return handle_render_home_page(request)

def handle_render_artwork_page(request):
    pass 

def artwork(request, artwork_id):
    art = Artwork.objects.get(art_id = artwork_id)

    if art.topic is not None:
        art.topic = [' > '.join(t.split('\\')) for t in art.topic]
    # art.notes = ".\n".join(art.notes)

    # record that the user has seen this artwork
    ArtworkVisited.objects.create(
        user = User.objects.get(user_id = request.session['user_id']),
        art = art,
        timestamp = timezone.now()
    )

    return render(request, 'museum_site/artwork.html', {
        'provided_consent': True, 'page_id': 'art_' + artwork_id,
        'artwork': art
    })

def handle_render_home_page(request):
    # art = Artwork.objects.order_by('?')[:5]
    art = Artwork.objects.all()[:5]
    return render(request, 'museum_site/index.html', {
        'provided_consent': True, 'page_id': 'index',
        # 'artwork': art
    })

@ensure_csrf_cookie
def save_rating(request):
    if request.method == 'POST':
        rating = request.POST['rating_number']
        user = request.session['user_id']
        artwork_id = request.POST['artwork_id']

        # get the artwork and user pair in question (or by the latest)
        art_visited = ArtworkVisited.objects.filter(
            user = user, art = artwork_id).latest('timestamp')
        art_visited.rating = rating 
        art_visited.save()
        
        return HttpResponse('ok')
    else:
        return HttpResponseBadRequest('rating not posted to backend')