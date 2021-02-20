from django.test import TestCase
from django.utils import timezone

from museum_site.models import User, UserDemographic

class UserTest(TestCase):
    def setUp(self) -> None:
        User.objects.create(
            # user id would normally be a uuid 
            user_id = 'user_1234', consent = True, email = 'test@email.com',
            contact_outcome = False, user_created = timezone.now()
        )

    def test_user_created(self):
        test_user = User.objects.get(user_id = 'user_1234')
        self.assertEqual(test_user.consent, True)
        self.assertEqual(test_user.email, 'test@email.com')
        self.assertEqual(test_user.contact_outcome, False)
    
class UserDemographicTest(TestCase):
    def setUp(self) -> None:
        User.objects.create(
            # user id would normally be a uuid 
            user_id = 'user_1234', consent = True, email = 'test@email.com',
            contact_outcome = False, user_created = timezone.now()
        )
        UserDemographic.objects.create(
            user = User.objects.get(user_id = 'user_1234'), 
            age = '21-29', gender = 'male', education = 'masters',
            work = 'employed', submission_timestamp = timezone.now()
        )
    
    def test_demographic_created(self):
        test_user = User.objects.get(user_id = 'user_1234')
        test_demo = UserDemographic.objects.get(user = test_user)
        self.assertEqual(test_demo.user, test_user)
        self.assertEqual(test_demo.age, '21-29'),
        self.assertEqual(test_demo.gender, 'male')
        self.assertEqual(test_demo.education, 'masters')
        self.assertEqual(test_demo.work, 'employed')

    def test_user_delete_cascade(self):
        # delete the user object from the database
        User.objects.get(user_id = 'user_1234').delete()
        self.assertFalse(User.objects.filter(user_id = 'user_1234').exists())

        # assert that the user doesn't exists in the demographic database
        self.assertFalse(UserDemographic.objects.filter(user_id = 'user_1234').exists())