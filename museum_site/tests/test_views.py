from django.test import TestCase
from django.urls import reverse

from museum_site.models import User 

class HandleInformationSheetViewTests(TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_user_created(self):
        user_count = User.objects.count()
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