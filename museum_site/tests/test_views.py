from django.test import TestCase
from django.test.utils import tag
from django.urls import reverse

from museum_site.models import User, UserDemographic 

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

        # check that the response contains the demographic form
        self.assertContains(response, 'demographic_form')
        self.assertTrue(response.context['load_demographic'])
        self.assertTrue(response.context['provided_consent'])

class HandleDemographicViewTest(TestCase):

    def setUp(self) -> None:
        # add the user to the session
        response_post = self.client.post(reverse('index'), data = {
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
        response = self.client.post(reverse('index'), data = post_data)
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
        response = self.client.post(reverse('index'), data = post_data)
        self.assertEqual(response.status_code, 200)

        # check that the correct variablues are being returned
        self.assertTrue(response.context['consent_required_before_demographic'])
        self.assertFalse(response.context['provided_consent'])
        self.assertIn('consent_form', response.context)