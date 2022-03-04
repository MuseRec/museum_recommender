from django.test import TestCase
from django.test.utils import tag
from django.urls import reverse
from django.utils import timezone

from museum_site.models import User, UserDemographic
from museum_site.models import Artwork, ArtworkVisited
from museum_site.models import UserCondition
from museum_site.views import get_condition
from collector.views import log


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

        # create artwork that can be passed to the front end
        self.artworks = [
            Artwork.objects.create(
                art_id="abcdef123456",
                collection="Collection 1",
                classification="Classification 1",
                title="Title 1",
                medium="Medium 1",
                artist='["Aaaa Bbbb"]',
                birth_date='["1880"]',
                death_date='["1950"]',
                earliest_date=1900,
                latest_date=1920,
                image_credit="Institution 1",
                linked_terms="['Term11', 'Term12', 'Term13']",
                linked_topics=['Topic11', 'Topic12', 'Topic13'],
                linked_art_terms="First group of trt terms",
                img_file="image_file_1.jpg",
                img_location="AAA/BBB/image_file_1.jpg",
            ),
            Artwork.objects.create(
                art_id="bcdefg234567",
                collection="Collection 2",
                classification="Classification 2",
                title="Title 2",
                medium="Medium 2",
                artist='["Aaaa Bbbb", "Cccc Dddd", "Eeee Ffff"]',
                birth_date='["1581", "1582", "1583", "1584"]',
                death_date='["1650", "1651", "1652", "1653"]',
                earliest_date=1600,
                latest_date=1620,
                image_credit="Institution 2",
                linked_terms="['Term21', 'Term22', 'Term23']",
                linked_topics=['Topic21', 'Topic22', 'Topic23'],
                linked_art_terms="Second group of trt terms",
                img_file="image_file_2.jpg",
                img_location="AAA/CCC/image_file_2.jpg",
            ),
            Artwork.objects.create(
                art_id="cdefgh345678",
                collection="Collection 3",
                classification="Classification 3",
                title="Title 3",
                medium="Medium 3",
                artist='["Eeee Ffff"]',
                birth_date='["1980"]',
                death_date=None,
                earliest_date=2000,
                latest_date=None,
                image_credit="Institution 3",
                linked_terms="['Term31', 'Term32', 'Term33']",
                linked_topics=['Topic31', 'Topic32', 'Topic33'],
                linked_art_terms="Third group of art terms",
                img_file="image_file_3.jpg",
                img_location="BBB/DDD/image_file_3.jpg",
            ),
        ]

    def test_artworks_are_returned(self):
        response = self.client.get(reverse('museum_site:index'))

        # test that the status code of the page is okay
        self.assertEqual(response.status_code, 200)

        # test that provided consent is returned as true
        self.assertTrue(response.context['provided_consent'])

        # there should be three artworks in the response
        self.assertEqual(len(response.context['page_obj']), 3)

        # and each of those should equal the ones we've created previously.
        for art in self.artworks:
            self.assertTrue(art in response.context['page_obj'])


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
