from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone

import uuid

from .forms import UserForm, UserDemographicForm
from .models import User, UserDemographic

def index(request):
    if request.method == 'POST':
        if 'information_sheet_form' in request.POST:
            return handle_information_sheet_post(request)
        elif 'demographic_form' in request.POST:
            return handle_demographic_post(request)
    else:
        if 'user_id' in request.session:
            return render(request, 'museum_site/index.html', {
                'provided_consent': True, 'page_id': 'index'
            })
        
        consent_form = UserForm()
        return render(request, 'museum_site/index.html', {
            'provided_consent': True, 'consent_form': consent_form,
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

        return render(request, 'museum_site/index.html', {
            'provided_consent': True, 'page_id': 'index'
        })