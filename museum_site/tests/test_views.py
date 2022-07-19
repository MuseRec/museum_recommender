from django.test import TestCase, override_settings
from django.test.utils import tag
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from museum_site.models import User, UserDemographic, UserCondition
from museum_site.models import Artwork, ArtworkVisited, ArtworkSelected
from museum_site.views import get_condition
from collector.views import log
from recommendations.models import DataRepresentation, Similarities


class IndexGetTest(TestCase):
    def test_consent_form_initial_visit(self):
        # test that the consent form is passed on the first visit of the user
        response = self.client.get(reverse('museum_site:index'))
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'museum_site/index.html')
        self.assertFalse(response.context['provided_consent'])

    def test_consent_with_user_in_session(self):
        # test that the provided consent has change and that the user is in the session
        # when they've provided the consent
        response_post = self.client.post(reverse('museum_site:index'), data={
            'information_sheet_form': 'information_sheet_form', 'email': 'test@email.com',
            'consent': True, 'contact_outcome': True
        })
        self.assertEqual(response_post.status_code, 200)

        u = User.objects.latest('user_created')

        response_get = self.client.get(reverse('museum_site:index'))
        self.assertEqual(response_get.status_code, 200)
        self.assertTrue(response_get.context['provided_consent'])
        self.assertEqual(response_get.context['page_id'], 'index')
        self.assertEqual(self.client.session['user_id'], u.user_id)


class HandleInformationSheetViewTest(TestCase):
    def test_user_created(self):
        post_data = {
            'information_sheet_form': 'information_sheet_form',
            'email': 'test@email.com', 'consent': True, 'contact_outcome': True
        }
        response = self.client.post(reverse('museum_site:index'), data=post_data)
        self.assertEqual(response.status_code, 200)

        # get the user that was just created
        u = User.objects.latest('user_created')

        # check that the user has been created
        self.assertEqual(u.email, 'test@email.com')
        self.assertEqual(u.consent, True)
        self.assertEqual(u.contact_outcome, True)

        # check that the user_id has been put into the session
        self.assertEqual(self.client.session['user_id'], u.user_id)

        # check that the response contains the demographic form
        self.assertContains(response, 'demographic_form')
        self.assertTrue(response.context['load_demographic'])
        self.assertTrue(response.context['provided_consent'])


class HandleDemographicViewTest(TestCase):
    def setUp(self) -> None:
        # add the user to the session
        response_post = self.client.post(reverse('museum_site:index'), data={
            'information_sheet_form': 'information_sheet_form', 'email': 'test@email.com',
            'consent': True, 'contact_outcome': True
        })
        self.assertEqual(response_post.status_code, 200)
        self.user = User.objects.latest('user_created')

    def test_demographic_created(self):
        post_data = {
            'demographic_form': 'demographic_form', 'age': '21-29', 'gender': 'male',
            'education': 'masters', 'work': 'employed'
        }
        response = self.client.post(reverse('museum_site:index'), data=post_data)
        self.assertEqual(response.status_code, 200)

        # get the demographic object just created
        d = UserDemographic.objects.latest('submission_timestamp')

        # check that the fields are correct
        self.assertEqual(d.age, '21-29')
        self.assertEqual(d.gender, 'male')
        self.assertEqual(d.education, 'masters')
        self.assertEqual(d.work, 'employed')

        # check that the correct user has been associated (fetched from the session)
        self.assertEqual(d.user, self.user)

        # ensure that the correct fields are being passed
        self.assertTrue(response.context['provided_consent'])
        self.assertEqual(response.context['page_id'], 'index')

    def test_consent_form_is_not_bypassed(self):
        # ensure that the consent form is returned if the user bypasses that step
        # and gets to the demographic form - we need consent before data is collected.

        # set the consent to false (forcing the else to be called in the view)
        self.user.consent = False
        self.user.save()

        post_data = {
            'demographic_form': 'demographic_form', 'age': '21-29', 'gender': 'male',
            'education': 'master', 'work': 'employed'
        }
        response = self.client.post(reverse('museum_site:index'), data=post_data)
        self.assertEqual(response.status_code, 200)

        # check that the correct variablues are being returned
        self.assertTrue(response.context['consent_required_before_demographic'])
        self.assertFalse(response.context['provided_consent'])
        self.assertIn('consent_form', response.context)


class HandleRenderHomePageTest(TestCase):
    def setUp(self) -> None:
        # add the user to the session
        response = self.client.post(reverse('museum_site:index'), data={
            'information_sheet_form': 'information_sheet_form', 'email': 'test@email.com',
            'consent': True, 'contact_outcome': True
        })
        self.assertEqual(response.status_code, 200)
        self.user = User.objects.latest('user_created')

        # change user condition to image
        uc = UserCondition.objects.get(user = self.user)
        uc.condition = 'image'
        uc.save()

        self.artworks = []
        for art in settings.INITIAL_ARTWORKS[:5]:
            self.artworks.append(Artwork.objects.create(
                art_id = art, collection = 'collection x', 
                classification = 'classification x', title = 'title', 
                medium = 'medium', artist = '["artist"]', 
                birth_date = '["1880"]', death_date = '["1950"]', 
                earliest_date = 1900, latest_date = 1920, 
                image_credit = 'institution', linked_terms = "['term 1', 'term 2', 'term 3']", 
                linked_topics = ['topic 1', 'topic 2', 'topic 3'], 
                linked_art_terms = 'group of terms', 
                img_file = 'image_file.jpg', 
                img_location = 'images/image_file.jpg'
            ))

        # create a fake data representation
        for representation in ['meta', 'image', 'concatenated']:
            DataRepresentation.objects.create(source = representation)
        self.representation = DataRepresentation.objects.get(source = 'image')

        # create some fake similarities
        fake_similarities = [
            (self.artworks[0], self.artworks[1]), # 0.8
            (self.artworks[0], self.artworks[2]), # 0.75
            (self.artworks[1], self.artworks[2]), # 0.5 
            (self.artworks[1], self.artworks[3]), # 1.0
            (self.artworks[4], self.artworks[0]) # 0.6
        ]
        scores = [0.8, 0.75, 0.5, 1.0, 0.6]
        self.sims = []
        for idx, (art_one, art_two) in enumerate(fake_similarities):
            sim = Similarities.objects.create(
                art = art_one, similar_art = art_two, 
                representation = self.representation, 
                score = scores[idx]
            )
            self.sims.append(sim)
        

    def test_artworks_are_returned(self):
        response = self.client.get(reverse('museum_site:index'))

        # test that the status code of the page is okay
        self.assertEqual(response.status_code, 200)

        # test that provided consent is returned as true
        self.assertTrue(response.context['provided_consent'])

        # there should be three artworks in the response
        self.assertEqual(len(response.context['artworks']), 20)

        # and each of those should equal the ones we've created previously.
        for art in self.artworks:
            self.assertTrue(art in response.context['artworks'])

    def test_random_context(self):
        # change the current context of the user to random
        user_condition = UserCondition.objects.get(user = self.user)
        user_condition.current_context = 'random'
        user_condition.save()

        # make the request (adds things to the cache etc)
        response = self.client.get(reverse('museum_site:index'))

        # select a few of the images
        for art in self.artworks[:3]:
            response_post = self.client.post(reverse('museum_site:selected'), data = {
                'artwork_id': art.art_id,
                'selection_button': ['Select']
            })
            self.assertEqual(response_post.status_code, 302)

        # update the user condition current step
        user_condition.current_step = user_condition.current_step + 1
        user_condition.save()

        # test that those selected have been removed
        response = self.client.get(reverse('museum_site:index'))

        artwork_response = response.context['artworks']

        self.assertNotIn(
            [art.art_id for art in self.artworks[:3]],
            [art.art_id for art in artwork_response]
        )

    @override_settings(CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_model_context(self):
        # change the current context of the user to model
        user_condition = UserCondition.objects.get(user = self.user)
        user_condition.current_context = 'model'
        user_condition.save()

        # make the request (adds things to the cache etc)
        response = self.client.get(reverse('museum_site:index'))
        print('response artworks', response.context['artworks'])

        
        # select the first artwork
        response_post = self.client.post(reverse('museum_site:selected'), data = {
            'artwork_id': self.artworks[0].art_id,
            'selection_button': ['Select']
        })
        self.assertEqual(response_post.status_code, 302)

        print('number of artworks', len(Artwork.objects.all()))
        print(ArtworkSelected.objects.all())
        print('Similarities', Similarities.objects.all())
        
        # update the user condition current step
        user_condition.current_step = user_condition.current_step + 1
        user_condition.save()

        # test that those selected have been removed
        response = self.client.get(reverse('museum_site:index'))

        print(response.context['artworks'])



class ArtworkTest(TestCase):
    def setUp(self) -> None:
        # add the user to the session
        response_post = self.client.post(reverse('museum_site:index'), data={
            'information_sheet_form': 'information_sheet_form', 'email': 'test@email.com',
            'consent': True, 'contact_outcome': True
        })
        self.assertEqual(response_post.status_code, 200)
        self.user = User.objects.latest('user_created')

        # create artwork (with null fields for simplicity)
        self.artwork, created = Artwork.objects.get_or_create(
            art_id="abcdef123456",
            title="Title 1",
            artist='["Aaaa Bbbb"]',
            img_file="image_file_1.jpg",
            img_location="BBB/DDD/image_file_1.jpg",
        )

    def test_that_artwork_is_returned(self):
        response = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['provided_consent'])
        self.assertEqual(response.context['page_id'], 'art_' + self.artwork.art_id)
        self.assertEqual(response.context['artwork'], self.artwork)

    def test_that_artwork_visited_object_is_created(self):
        response = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))
        self.assertEqual(response.status_code, 200)
        av = ArtworkVisited.objects.latest('timestamp')
        self.assertEqual(av.user, self.user)
        self.assertEqual(av.art, self.artwork)

    # def test_that_topics_are_correctly_split(self):
    #     response = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))
    #     self.assertEqual(response.status_code, 200)
    #
    #     # get the original artwork from the database
    #     org_artwork = Artwork.objects.get(art_id=self.artwork.art_id)
    #
    #     split_topic = response.context['artwork'].topic
    #     self.assertEqual(len(org_artwork.topic), len(split_topic))

    def test_that_rating_is_returned_when_previously_rated(self):
        # visit the artwork
        visit_respose = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))
        self.assertEqual(visit_respose.status_code, 200)

        # post the rating to the backend
        response = self.client.post(
            reverse('museum_site:rating'),
            data={'artwork_id': self.artwork.art_id, 'rating_number': 5}
        )
        self.assertEqual(response.status_code, 200)

        # visit the artwork and check that the rating is in the response
        response = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['artwork_rating'], '5')


class SaveRatingTest(TestCase):
    def setUp(self) -> None:
        # add the user to the session
        response_post = self.client.post(reverse('museum_site:index'), data={
            'information_sheet_form': 'information_sheet_form', 'email': 'test@email.com',
            'consent': True, 'contact_outcome': True
        })
        self.assertEqual(response_post.status_code, 200)
        self.user = User.objects.latest('user_created')

        # create artwork (with null fields for simplicity)
        self.artwork, created = Artwork.objects.get_or_create(
            art_id="abcdef123456",
            title="Title 1",
            artist='["Aaaa Bbbb"]',
            img_file="image_file_1.jpg",
            img_location="BBB/DDD/image_file_1.jpg",
        )

        self.artwork_visited, _ = ArtworkVisited.objects.get_or_create(
            user=self.user, art=self.artwork, timestamp=timezone.now()
        )

    def test_get_bad_request(self):
        response = self.client.get(reverse('museum_site:rating'))
        self.assertEqual(response.status_code, 400)

    def test_post_rating_successful(self):
        response = self.client.post(
            reverse('museum_site:rating'),
            data={'artwork_id': self.artwork.art_id, 'rating_number': 5}
        )
        self.assertEqual(response.status_code, 200)

        # check that the object has been created
        av = ArtworkVisited.objects.filter(user=self.user, art=self.artwork).latest('timestamp')
        self.assertEqual(av.user, self.user)
        self.assertEqual(av.art, self.artwork)
        self.assertEqual(av.rating, 5)

    def test_that_most_recent_object_is_updated(self):
        # add a visit where the user rates the artwork
        _ = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))
        response = self.client.post(
            reverse('museum_site:rating'),
            data={'artwork_id': self.artwork.art_id, 'rating_number': 1})
        self.assertEqual(response.status_code, 200)

        # add another couple of visits
        _ = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))
        _ = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))

        # visit again, store a new rating
        visit_respose = self.client.get(reverse('museum_site:artwork', args=[self.artwork.art_id]))
        rating_response = self.client.post(
            reverse('museum_site:rating'),
            data={'artwork_id': self.artwork.art_id, 'rating_number': 4}
        )
        self.assertEqual(visit_respose.status_code, 200)
        self.assertEqual(rating_response.status_code, 200)

        # check that the most recent object is updated
        self.assertEqual(
            ArtworkVisited.objects.filter(
                user=self.user, art=self.artwork).latest('timestamp').rating, 4
        )

        # check that the other objects haven't been updated
        av_set = ArtworkVisited.objects.all().order_by('timestamp')
        for av, rating in zip(av_set, [None, 1, None, None, 4]):  # first none due to setUp
            self.assertEqual(av.rating, rating)
