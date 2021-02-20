from django.test import TestCase
from django.utils import timezone
from museum_site.forms import UserDemographicForm, UserForm
from museum_site.models import User

class UserFormTest(TestCase):
    def test_form_create(self):
        form_data = dict(
            user_id = 'user_1234', consent = True, email = 'test@email.com',
            contact_outcome = False, user_created = timezone.now()
        )
        form = UserForm(data = form_data)
        self.assertTrue(form.is_valid())

    def test_missing_consent_field(self):
        form_data = dict(
            user_id = 'user_1234', email = 'test@email.com', contact_outcome = True,
            user_created = timezone.now()
        )
        form = UserForm(data = form_data)
        self.assertFalse(form.is_valid())

    def test_missing_email_when_contact_true(self):
        form_data = dict(
            user_id = 'user_1234', consent = True, email = '',
            contact_outcome = True, user_created = timezone.now()
        )
        form = UserForm(data = form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['email'][0], 'Email is required if you want to be contacted')

class UserDemographicFormTest(TestCase):
    def setUp(self) -> None:
        User.objects.create(
            # user id would normally be a uuid 
            user_id = 'user_1234', consent = True, email = 'test@email.com',
            contact_outcome = False, user_created = timezone.now()
        )
    
    def test_form_create(self):
        form_data = dict(
            user = User.objects.get(user_id = 'user_1234'), age = '21-29', gender = 'male',
            education = 'masters', work = 'employed', submission_timestamp = timezone.now()
        )
        form = UserDemographicForm(data = form_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_field(self):
        form_data = dict(
            user = User.objects.get(user_id = 'user_1234'), age = '21-29', gender = 'male',
            education = 'masters', submission_timestamp = timezone.now()
        ) # missing the work field
        form = UserDemographicForm(data = form_data)
        self.assertFalse(form.is_valid())

    