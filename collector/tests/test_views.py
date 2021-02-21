from django.test import TestCase 
from django.utils import timezone
from django.urls import reverse

from collector.models import Interaction
from museum_site.models import User

class LogViewTest(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(
            user_id = 'user_1234', consent = True, email = 'test@email.com',
            contact_outcome = False, user_created = timezone.now()
        )
        session = self.client.session 
        session['user_id'] = self.user.user_id
        session.save()

    def test_get_response(self):
        response = self.client.get(reverse('interaction_logger'))
        self.assertEqual(response.status_code, 400)
        
    def test_post_request_object_created(self):
        response_post = self.client.post(
            reverse('interaction_logger'),
            data = {
                'content_id': 'artwork_1234', 'event_type': 'click', 'page_id': 'index'
            }
        )
        self.assertEqual(response_post.status_code, 200)

        interaction = Interaction.objects.latest('timestamp')
        self.assertEqual(interaction.content_id, 'artwork_1234')
        self.assertEqual(interaction.event, 'click')
        self.assertEqual(interaction.page, 'index')
        self.assertEqual(interaction.user, self.user)

    def test_post_request_when_event_is_home_button(self):
        response_post = self.client.post(
            reverse('interaction_logger'),
            data = {
                'content_id': 'home-button', 'event_type': 'click', 'page_id': 'index'
            },
            follow = True
        )
        self.assertEqual(response_post.status_code, 200)
        self.assertRedirects(
            response_post, expected_url = reverse('index'), 
            status_code = 302, target_status_code = 200
        )
