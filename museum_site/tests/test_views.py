from django.test import TestCase
from django.urls import reverse

from museum_site.models import User 

class IndexGetTest(TestCase):

    def test_consent_form_initial_visit(self):
        # test that the consent form is passed on the first visit of the user
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'museum_site/index.html')
        self.assertFalse(response.context['provided_consent'])

    def test_consent_with_user_in_session(self):
        # test that the provided consent has change and that the user is in the session
        # when theye've provided the consent
        response_post = self.client.post(reverse('index'), data = {
            'information_sheet_form': 'information_sheet_form', 'email': 'test@email.com',
            'consent': True, 'contact_outcome': True 
        })
        self.assertEqual(response_post.status_code, 200)

        u = User.objects.latest('user_created')

        response_get = self.client.get(reverse('index'))
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
        response = self.client.post(reverse('index'), data = post_data)
        self.assertEqual(response.status_code, 200)

        # get the user that was just created
        u = User.objects.latest('user_created')

        # check that the user has been created
        self.assertEqual(u.email, 'test@email.com')
        self.assertEqual(u.consent, True)
        self.assertEqual(u.contact_outcome, True)

        # check that the user_id has been put into the session
        self.assertEqual(self.client.session['user_id'], u.user_id)

class HandleDemographicViewTest(TestCase):
    pass