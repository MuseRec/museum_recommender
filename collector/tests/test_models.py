from django.test import TestCase 
from django.utils import timezone

from collector.models import Interaction
from museum_site.models import User 

class InteractionTest(TestCase):
    def setUp(self) -> None:
        # create a user to associate the interaction events to
        self.user = User.objects.create(
            user_id = 'user_1234', consent = True, email = 'test@email.com',
            contact_outcome = False, user_created = timezone.now()
        )

    def test_interaction_created(self):
        interaction = Interaction(
            user = self.user, timestamp = timezone.now(), content_id = 'home-button',
            event = 'click', page = 'index'
        )
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.content_id, 'home-button')
        self.assertEqual(interaction.event, 'click')
        self.assertEqual(interaction.page, 'index')        

    def test_interaction_cascade_on_user_delete(self):
        # create the interaction event
        Interaction.objects.create(
            user = self.user, timestamp = timezone.now(), content_id = 'home-button',
            event = 'click', page = 'index'
        ) 

        # delete the user from the database
        self.user.delete()
        self.assertFalse(User.objects.filter(user_id = self.user.user_id).exists())

        # assert that there are no interaction events with that user
        self.assertFalse(Interaction.objects.filter(user = self.user).exists())
    
    