from itertools import count
from statistics import mode
from tkinter import N
from django.http.response import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.conf import settings
from django.core.cache import cache

import uuid
import operator
import json
from itertools import chain 

from .forms import DistractionTaskForm, UserForm, UserDemographicForm, DomainKnowledgeForm
from .forms import SelectedArtworkForm, StudyTransitionForm, PostStudyForm, PostStudyGeneralForm
from .models import User, UserDemographic, Artwork, ArtworkVisited
from .models import UserCondition, ArtworkSelected, RecommendedArtwork
from collector.models import Interaction
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
        elif 'distraction_form' in request.POST:
            return handle_distraction_task(request)
    else:
        if 'user_id' in request.session:
            if 'distraction_task' in request.session:
                return render(
                    request, 'museum_site/index.html', {
                        'provided_consent': True, 
                        'provided_demographics': True, 
                        'study_context': settings.CONTEXT,
                        'load_domain': False, 
                        'load_distraction': True,
                        'distraction_form': DistractionTaskForm()
                    }
                )

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

        print('condition', condition)
        print('order', order)

        UserCondition.objects.create(
            user = new_user, 
            condition = condition,
            order = order,
            current_context = 'initial',
            current_step = 1,
            timestamp = timezone.now()
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

    user = User.objects.get(user_id = request.session['user_id'])
    user_condition = UserCondition.objects.get(user = user)

    # record that the user has seen this artwork
    ArtworkVisited.objects.create(
        user=user,
        art=art,
        timestamp=timezone.now()
    )

    if request.session.get('reset_current_step_count'):
        selection_count = 0 
        request.session['reset_current_step_count'] = False
    else:
        selected_artwork = ArtworkSelected.objects.filter(
            user = user, selection_context = user_condition.current_context
        )
        selection_count = selected_artwork.count()
    # get the artwork that the user has selected
    # if cache.get('current_step'):
    #     selected_artwork = ArtworkSelected.objects.filter(
    #         user = user, selection_context = user_condition.current_context, 
    #         current_step = cache.get('current_step')
    #     )
    # else:
    # selected_artwork = ArtworkSelected.objects.filter(
    #     user = user, selection_context = user_condition.current_context
    # )
    # print('selected artwork', selected_artwork.count())
    if cache.get('current_step'):
        selected_artwork = ArtworkSelected.objects.filter(
            user = user, selection_context = user_condition.current_context, 
            step_selected = cache.get('current_step')
        )
    else:
        selected_artwork = ArtworkSelected.objects.filter(
            user = user, selection_context = user_condition.current_context
        )


    # get the artworks that the user has already selected (to grey out the button)
    already_selected = {art.selected_artwork.art_id for art in selected_artwork}

    context = {
        'provided_consent': True, 'page_id': 'art_' + artwork_id,
        'artwork': art,
        'artists': artists,
        'artwork_rating': str(artwork_rating),
        'study_context': settings.CONTEXT,
        'selection_count': selected_artwork.count(),
        'already_selected': already_selected,
        'too_many_selected': request.session.get('too_many_selected', False),
        'is_artwork_page': True
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
    # THIS IS WHERE WE LAND ONCE THE USER HAS DONE ALL OF THE 
    # INITIAL QUESTIONAIRES. 
    # WE NEED TO SEND BACK EITHER THE RANDOM OR MODEL-BASED IMAGES.

    # initially, a set of 20 artworks should be shown to the user at random (the same to all users).
    # 
    # the user then selects five, and based on these, they are shown another 15 (random or recs)

    user = User.objects.get(user_id = request.session['user_id'])
    user_condition = UserCondition.objects.get(user = user)

    if user_condition.current_context == 'initial':
        # get the artworks if they're stored in the cache
        artworks = cache.get('artworks')

        # if there aren't any stored artworks, i.e., the first the user joins
        if artworks is None:
            # get the artworks that are in the initial set and randomise
            artworks = Artwork.objects.filter(art_id__in = settings.INITIAL_ARTWORKS).order_by('?')

            # store them in the cache, without a timeout.
            cache.set('artworks', artworks, timeout = None)

            # also store in the session what the current context is (to check later)
            cache.set('current_context', user_condition.current_context, timeout = None)

        # if show_instructions is not in the session context, then they've not seen it yet.
        if 'show_instructions' not in request.session:
            # set to true to trigger the instructions being shown
            request.session['show_instructions'] = True 
        else: # otherwise, it is and they have.
            # set to false to prevent them bein shown again
            request.session['show_instructions'] = False 
    elif user_condition.current_context == 'random':
        # we get the artwork query set in a random way - but should remain the same
        # when the page is refreshed

        # get the artworks and current context
        artworks = cache.get('artworks')
        cached_current_context = cache.get('current_context')

        # if the cached current context is not random, then the user is entering a new condition
        if cached_current_context != 'random':
            # get a random set of 30 artworks 
            artworks = Artwork.objects.order_by('?')[:30]

            # save the artworks, with the user, and the condition in the database
            for art_work in artworks:
                RecommendedArtwork.objects.create(
                    user = user, 
                    recommended_artwork = art_work, 
                    recommendation_context = 'random'
                )

            # update the artwork and current context in the cache
            cache.set('artworks', artworks, timeout = None)
            cache.set('current_context', 'random', timeout = None)
            
            # add the current step into the cache to keep track
            cache.set('current_step', 1, timeout = None)

        print('CURRENT STEP', user_condition.current_step)

        # if these aren't equal, then it means that hte user has moved along into another step 
        if cache.get('current_step') != user_condition.current_step:
            # get all the artworks that hte user has selected for this condition
            selected_artworks = {
                selected_art.selected_artwork.art_id
                for selected_art in ArtworkSelected.objects.filter(
                    user = user, selection_context = 'random'
                )
            }

            print('selected', selected_artworks)

            # record how many artworks there are pre-filtering
            pre_filter_length = len(artworks)

            # filter those out that have been previously selected
            artworks_filtered = [
                art for art in artworks 
                if art.art_id not in selected_artworks
            ]

            print('filtered', [a.art_id for a in artworks_filtered])

            # replace those that have been removed with other artworks
            number_to_replace = pre_filter_length - len(artworks_filtered)

            print('number to replace', number_to_replace)

            # get the new set of artworks
            new_set = Artwork.objects.exclude( # we don't want those already selected
                art_id__in = selected_artworks
            ).exclude( # nor those we already have
                art_id__in = [a.art_id for a in artworks_filtered]
            ).order_by('?')[:number_to_replace] # randomise and get the number we want

            print('new set', [n.art_id for n in new_set])

            # bring the two sets together 
            artworks = list(chain(artworks_filtered, new_set))

            print('artworks', artworks)

            # update the cache
            cache.set('artworks', artworks, timeout = None)
            cache.set('current_step', cache.get('current_step') + 1, timeout = None)
    else:
        assert user_condition.current_context == 'model'

        # get the artworks and current context 
        artworks = cache.get('artworks')
        cached_current_context = cache.get('current_context')

        # if the cached current context is not model, then the user is entering this condition
        # for the first time.
        if cached_current_context != 'model':
            # get the selected artworks by the user
            selected_artworks = [
                selected_art.selected_artwork
                for selected_art in ArtworkSelected.objects.filter(
                    user = user, selection_context = 'initial'
                )
            ]

            # get the model condition that the user should see (either meta, image, or concatenated)
            model_condition = DataRepresentation.objects.get(source = user_condition.condition)

            # get the similar artworks based on those selected and the representation, order 
            # by the score (descending), and take the top 30
            artworks = Similarities.objects.filter(
                representation = model_condition, art__in = selected_artworks
            ).order_by('-score')[:30]

            # get the artworks themselves 
            artworks = [s_a.similar_art for s_a in artworks]

            # save the artworks, with the user and the condition, in the database
            for art_work in artworks:
                RecommendedArtwork.objects.create(
                    user = user, 
                    recommended_artwork = art_work, 
                    recommendation_context = 'random'
                )
            
            # update the artwork and current context in the cache
            cache.set('artworks', artworks, timeout = None)
            cache.set('current_context', 'model', timeout = None)
 
    # convert the artist list
    for art in artworks:
        if art.artist:
            try: 
                artist_list = json.loads(art.artist)
            except json.decoder.JSONDecodeError:
                artist_list = art.artist.split(',')[0]
            
            if len(artist_list) > 1:
                art.artist = ', '.join(artist_list)
            else:
                art.artist = artist_list[0]
        else:
            art.artist = 'unknown artist'

    
    # selected_artwork = ArtworkSelected.objects.filter(
    #     user = user, selection_context = user_condition.current_context
    # )
    # selection_count = 0 if reset_current_step_count else selected_artwork.count()

    if cache.get('current_step'):
        print('current step', cache.get('current_step'))
        selected_artwork = ArtworkSelected.objects.filter(
            user = user, selection_context = user_condition.current_context, 
            step_selected = cache.get('current_step')
        )
        print('number of selected artworks', selected_artwork.count())
    else:
        print('not in a step')
        selected_artwork = ArtworkSelected.objects.filter(
            user = user, selection_context = user_condition.current_context
        )

    # get the artworks that the user has already selected (to grey out)
    already_selected = {art.selected_artwork.art_id for art in selected_artwork}
    

    if settings.CONTEXT == 'focus':
        paginator = Paginator(artworks, 30)
        page_number = request.GET.get('page')
        artworks = paginator.get_page(page_number)

    # if show_reminder is in the session, then set a flag to say they're about to see it 
    # if that flag is there, then set the show reminder as false
    if 'show_reminder' in request.session and 'reminder_seen' not in request.session:
        # set a flag for when the page reloads on each artwork selection
        request.session['reminder_seen'] = True 
    elif 'show_reminder' in request.session and 'reminder_seen' in request.session:
        # set it to false as they will have seen it if the condition above is met.
        request.session['show_reminder'] = False


    context = {
        'provided_consent': True, 'page_id': 'index',
        'artworks': artworks,
        'study_context': settings.CONTEXT,
        'selection_context': user_condition.current_context,
        'selection_count': selected_artwork.count(),
        'already_selected': already_selected,
        'show_instructions': request.session.get('show_instructions', False),
        'show_reminder': request.session.get('show_reminder', False)
    }

    return render(request, 'museum_site/index.html', context)


def selected_artwork(request):
    if request.method == 'POST':
        form = SelectedArtworkForm(request.POST)
        if form.is_valid():
            user = User.objects.get(user_id = request.session['user_id'])
            artwork = Artwork.objects.get(art_id = request.POST['artwork_id'])
            user_condition = UserCondition.objects.get(user = user)
            timestamp = timezone.now()

            if form.cleaned_data['selection_button'] == 'Select':
                current_step = -1 if not cache.get('current_step') else cache.get('current_step')

                # get the number of artworks that the user has already selected
                number_selected = ArtworkSelected.objects.filter(
                    user = user, selection_context = user_condition.current_context, 
                    step_selected = cache.get('current_step')
                ).count()

                # if the number of selected artworks is greater than the upper bound
                if number_selected >= settings.SELECTION_UPPER_BOUND:
                    request.session['too_many_selected'] = True
                    return redirect('museum_site:artwork', artwork_id = artwork.art_id)

                current_step = cache.get('current_step')

                # save that the user has selected the artwork
                ArtworkSelected.objects.create(
                    user = user, 
                    selected_artwork = artwork,
                    selection_context = user_condition.current_context, 
                    step_selected = -1 if not cache.get('current_step') else cache.get('current_step'),
                    timestamp = timestamp
                )

                # save it as an interaction event
                Interaction.objects.create(
                    user = user, 
                    timestamp = timestamp, 
                    content_id = artwork.art_id, 
                    event = 'artwork-selected',
                    page = 'art_' + artwork.art_id
                )

                return redirect('museum_site:artwork', artwork_id = artwork.art_id)
            else: 
                assert form.cleaned_data['selection_button'] == 'Deselect'

                # delete the record from the database
                ArtworkSelected.objects.filter(user = user, selected_artwork = artwork).delete()

                # save it as an interaction event 
                Interaction.objects.create(
                    user = user,
                    timestamp = timestamp, 
                    content_id = artwork.art_id, 
                    event = 'artwork-deselected',
                    page = 'art_' + artwork.art_id
                )

                return redirect('museum_site:artwork', artwork_id = artwork.art_id)

def transition_study_stage(request):
    # print('transition clicked')
    if request.method == 'POST' and 'load_post_study' not in request.session:
        form = StudyTransitionForm(request.POST)
        if form.is_valid():
            user = User.objects.get(user_id = request.session['user_id'])
            user_condition = UserCondition.objects.get(user = user)
            selection_count = ArtworkSelected.objects.filter(
                user = user, selection_context = user_condition.current_context, 
                step_selected = -1 if not cache.get('current_step') else cache.get('current_step')
            ).count()

            # print('current user condition:', user_condition.current_context)

            # if the number of artworks selected is between the lower and upper bound
            within_bounds = settings.SELECTION_LOWER_BOUND <= selection_count <= settings.SELECTION_UPPER_BOUND

            # if the number of artworks selected is between the lower and upper bound
            if (within_bounds and user_condition.current_context == 'initial'):
                # and if the user is current in the initial context (just starting the study)
                # if user_condition.current_context == 'initial':
                # then we need to set their current context based on the first condition
                # the user should see (either random or model)
                if user_condition.order == 'random':
                    user_condition.current_context = 'random'
                else:
                    user_condition.current_context = 'model'
                user_condition.save() # update the user condition record in the DB

                # redirect to the index; the updated user condition will change the 
                # artworks that the user sees.
                return redirect('museum_site:index')
                # otherwise, they're transitioning between part one and two or to part-two -> end 
            elif (within_bounds and user_condition.current_step == settings.NUMBER_OF_STEPS):
                if user_condition.current_context == 'random' and user_condition.order == 'random':
                    # we need to update their current context to 'model', reset their
                    # current step to 1, and save it
                    user_condition.current_context = 'model'
                    user_condition.current_step = 1
                    user_condition.save()

                    print('updated context to', user_condition.current_context)

                    request.session['distraction_task'] = True

                    # redirect to the index
                    return redirect('museum_site:index')
                # if their context is model and first condition is model
                elif user_condition.current_context == 'model' and user_condition.order == 'model':
                    # we need to update their current context to 'random', reset their
                    # current step to 1, and save it
                    user_condition.current_context = 'random'
                    user_condition.current_step = 1
                    user_condition.save()

                    request.session['distraction_task'] = True

                    # redirect to the index
                    return redirect('museum_site:index')
                # otherwise, they're at the end of the study and the post-study questionnaires
                # should be rendered
                else: # this is the final part.
                    request.method = 'GET'
                    return redirect('museum_site:post-study', which_form = 'part_one')
            elif within_bounds:
                # state remains the same
                # update the number of steps (+1)
                user_condition.current_step = user_condition.current_step + 1
                user_condition.save()
                return redirect('museum_site:index')

                    
def handle_distraction_task(request):
    distraction_form = DistractionTaskForm(request.POST)
    if distraction_form.is_valid():
        new_submission = distraction_form.save(commit = False)
        
        # assign the user and the submission timestamp
        new_submission.user = User.objects.get(user_id = request.session['user_id'])
        new_submission.submission_timestamp = timezone.now()

        new_submission.save()

        del request.session['distraction_task']

        # add in the flag to bring up the 'reminder' of the instructions.
        request.session['show_reminder'] = True

        return handle_render_home_page(request)

def post_study(request, which_form):
    if request.method == 'POST':
        study_id = request.POST['study_id']

        if study_id == 'general':
            print('posting general')
            post_study_form = PostStudyGeneralForm(request.POST)
        else:
            print('posting', study_id)
            post_study_form = PostStudyForm(request.POST)

        if post_study_form.is_valid():
            new_submission = post_study_form.save(commit = False)

            # assign the user, submission timestamp, and the part
            new_submission.user = User.objects.get(user_id = request.session['user_id'])
            new_submission.submission_timestamp = timezone.now()

            if study_id != 'general':
                new_submission.part = study_id

            new_submission.save()

            print('saved!')

            if study_id != 'general':
                if study_id == 'part_two':
                    # they've done both part one and two, now load the general form
                    return redirect('museum_site:post-study', which_form = 'general')
                else:
                    # otherwise we want to just load part two.
                    return redirect('museum_site:post-study', which_form = 'part_two')
            else:
                # we render the thank you page
                return redirect('museum_site:thank-you') 
    else:
        # if it's a request for general form, then return that
        if which_form == 'general':
            print('which form == general')
            return render(request, 'museum_site/post_study.html', {
                'post_study_form': PostStudyGeneralForm(),
                'part': 'general'    
            })
        elif which_form == 'part_two':
            print('which form == part_two')
            return render(request, 'museum_site/post_study.html', {
                'post_study_form': PostStudyForm(), 
                'part': 'part_two'
            })
        else:
            print('which form == part_one')
            return render(request, 'museum_site/post_study.html', {
                'post_study_form': PostStudyForm(), 
                'part': 'part_one'
            })

def thank_you(request):
    return render(request, 'museum_site/thankyou.html')

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



    # if there is a search request
    # query = None
    # if request.GET.get('search'):
    #     query = request.GET.get('search').strip()
    #     art = Artwork.objects.filter(
    #         Q(title__icontains=query)
    #         | Q(artist__icontains=query)
    #         | Q(medium__icontains=query)
    #         | reduce(operator.or_, (Q(title__icontains = x) for x in query.split(' ')))
    #         | reduce(operator.or_, (Q(artist__icontains = x) for x in query.split(' ')))
    #         | reduce(operator.or_, (Q(medium__icontains=x) for x in query.split(' ')))
    #     )
    #     # art = Artwork.objects.filter(
    #     #     complex_query(query, "title") |
    #     #     complex_query(query, "artist") |
    #     #     complex_query(query, "medium")
    #     # )
    # else:
    #     art = Artwork.objects.all()

    # Convert ot list
    # for e in art:
    #     if e.artist:
    #         if e.artist.find("unknown") != -1:
    #             # e.artist = ["Unknown artist"]
    #             e.artist = "Unknown artist"
    #         else:
    #             e.artist = ", ".join(json.loads(e.artist))