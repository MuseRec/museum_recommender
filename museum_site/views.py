from itertools import count
from django.http.response import HttpResponseBadRequest
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.conf import settings

import uuid
import operator
import json
from functools import reduce

from .forms import UserForm, UserDemographicForm, DomainKnowledgeForm
from .models import User, UserDemographic, Artwork, ArtworkVisited, DomainKnowledge, UserCondition
from recommendations.models import Similarities, DataRepresentation
from .util import get_condition, get_order

def index(request):
    if (request.method == 'POST') and (settings.CONTEXT == 'user'):
        if 'information_sheet_form' in request.POST:
            return handle_information_sheet_post(request)
        elif 'demographic_form' in request.POST:
            # check that the user has provided consent in the prior step before
            # progressing with collecting their data
            if User.objects.get(user_id=request.session['user_id']).consent:
                return handle_demographic_post(request)
            else:
                # if they haven't, then reload the page with the consent form
                return render(request, "museum_site/index.html", {
                    'provided_consent': False, 'consent_form': UserForm(),
                    'consent_required_before_demographic': True,
                    'study_context': settings.CONTEXT
                })
        elif 'domain_form' in request.POST:
            if User.objects.get(user_id = request.session['user_id']).consent:
                return handle_domain_knowledge_post(request)
            else:
                return render(request, "museum_site/index.html", {
                    'provided_consent': False, 'consent_form': UserForm(), 
                    'consent_required_before_demographic': True,
                    'study_context': settings.CONTEXT
                })
    else:
        if 'user_id' in request.session:
            return handle_render_home_page(request)
        
        # if the context is the focus group
        if settings.CONTEXT == 'focus':
            # and the user doesn't exist, then we need to create one.
            if not 'user_id' in request.session:
                User.objects.create(
                    user_id = 'focus-group-user',
                    consent = True, 
                    email = 'focus@group.com',
                    contact_outcome = True,
                    user_created = timezone.now()
                )
                request.session['user_id'] = 'focus-group-user'

            return handle_render_home_page(request)

        print('returning the user form')
        consent_form = UserForm()
        return render(request, "museum_site/index.html", {
            'provided_consent': False, 'consent_form': consent_form,
            'study_context': settings.CONTEXT
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

        # assign to a condition and order 
        condition = get_condition()
        order = get_order()
        UserCondition.objects.create(
            user = new_user, 
            condition = condition,
            order = order
        )

        # now load the demographic survey
        demographic_form = UserDemographicForm()

        return render(request, "museum_site/index.html", {
            'provided_consent': True, 'demographic_form': demographic_form,
            'load_demographic': True, 'study_context': settings.CONTEXT
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
        # return handle_render_home_page(request)

        domain_form = DomainKnowledgeForm()

        return render(request, "museum_site/index.html", {
            'provided_consent': True, 'provided_demographics': True, 
            'domain_form': domain_form, 'load_domain': True,
            'study_context': settings.CONTEXT
        })

def handle_domain_knowledge_post(request):
    domain_form = DomainKnowledgeForm(request.POST)
    if domain_form.is_valid():
        new_domain = domain_form.save(commit = False)

        # assign the user and submission timestamp
        new_domain.user = User.objects.get(user_id = request.session['user_id'])
        new_domain.submission_timestamp = timezone.now()

        new_domain.save()

        return handle_render_home_page(request)


def artwork(request, artwork_id):
    art = Artwork.objects.get(art_id=artwork_id)

    # if the user has previously visited the artwork, then get the rating
    av = ArtworkVisited.objects.filter(user=request.session['user_id'], art=artwork_id)
    if av:
        artwork_rating = av.latest('timestamp').rating
    else:
        artwork_rating = None

    # Convert JSON types to lists
    if art.artist:
        if any(e.find("unknown") != -1 for e in json.loads(art.artist)):
            art.artist = [(0, "Unknown artist")]
        else:
            art.artist = [(i, e) for i, e in enumerate(json.loads(art.artist))]
    if art.birth_date:
        art.birth_date = [(i, e) for i, e in enumerate(json.loads(art.birth_date))]
    if art.death_date:
        art.death_date = [(i, e) for i, e in enumerate(json.loads(art.death_date))]
    if art.medium:
        art.medium = json.loads(art.medium)
    if art.linked_topics:
        art.linked_topics = json.loads(art.linked_topics)
    if art.linked_terms:
        art.linked_terms = json.loads(art.linked_terms)

    artists = None
    if len(art.artist) > 1 and \
            (art.birth_date is not None and len(art.artist) == len(art.birth_date)) and \
            (art.death_date is not None and len(art.artist) == len(art.death_date)):
        artists = ["{0} ({1} - {2})".format(n[1], db[1], dd[1])
                   for n, db, dd in zip(*[art.artist, art.birth_date, art.death_date])]

    # record that the user has seen this artwork
    ArtworkVisited.objects.create(
        user=User.objects.get(user_id=request.session['user_id']),
        art=art,
        timestamp=timezone.now()
    )

    context = {
        'provided_consent': True, 'page_id': 'art_' + artwork_id,
        'artwork': art,
        'artists': artists,
        'artwork_rating': str(artwork_rating),
        'study_context': settings.CONTEXT,
    }

    # fetch the top 5 most similar artworks to this one, if the context is the focus group
    if settings.CONTEXT == 'focus':
        result_set = Similarities.objects.filter(
            art = art, 
            representation = DataRepresentation.objects.get(source = settings.DATA_REP_TYPE)
        )[:5]
        context['similar_artworks'] = result_set

    return render(request, "museum_site/artwork.html", context)


def handle_render_home_page(request):
    # 

    # if there is a search request
    query = None
    if request.GET.get('search'):
        query = request.GET.get('search').strip()
        art = Artwork.objects.filter(
            Q(title__icontains=query)
            | Q(artist__icontains=query)
            | Q(medium__icontains=query)
            | reduce(operator.or_, (Q(title__icontains = x) for x in query.split(' ')))
            | reduce(operator.or_, (Q(artist__icontains = x) for x in query.split(' ')))
            | reduce(operator.or_, (Q(medium__icontains=x) for x in query.split(' ')))
        )
        # art = Artwork.objects.filter(
        #     complex_query(query, "title") |
        #     complex_query(query, "artist") |
        #     complex_query(query, "medium")
        # )
    else:
        art = Artwork.objects.all()

    # Convert ot list
    # for e in art:
    #     if e.artist:
    #         if e.artist.find("unknown") != -1:
    #             # e.artist = ["Unknown artist"]
    #             e.artist = "Unknown artist"
    #         else:
    #             e.artist = ", ".join(json.loads(e.artist))

    # convert the artist list
    for artwork in art:
        if artwork.artist:
            try: 
                artist_list = json.loads(artwork.artist)
            except json.decoder.JSONDecodeError:
                artist_list = artwork.artist.split(',')[0]
            
            if len(artist_list) > 1:
                artwork.artist = ', '.join(artist_list)
            else:
                artwork.artist = artist_list[0]
        else:
            artwork.artist = 'unknown artist'
    
    paginator = Paginator(art, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'museum_site/index.html', {
        'provided_consent': True, 'page_id': 'index',
        'page_obj': page_obj,
        'search': None if query is None or len(query) == 0 else query,
        'study_context': settings.CONTEXT,
    })


@ensure_csrf_cookie
def save_rating(request):
    if request.method == 'POST':
        rating = request.POST['rating_number']
        user = request.session['user_id']
        artwork_id = request.POST['artwork_id']

        # get the artwork and user pair in question (or by the latest)
        art_visited = ArtworkVisited.objects.filter(
            user=user,
            art=artwork_id
        ).latest('timestamp')
        art_visited.rating = rating
        art_visited.save()
        return HttpResponse('ok')
    else:
        return HttpResponseBadRequest('rating not posted to backend')
