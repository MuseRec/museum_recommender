
from django.test import TestCase
from django.utils import timezone
from django.conf import settings

from museum_site.models import UserCondition, User
from museum_site.util import get_condition, get_order

class GetConditionTest(TestCase):
    
    def test_no_saved_conditions(self):
        condition, weights = get_condition()

        self.assertTrue(isinstance(condition, str))
        self.assertTrue(condition in settings.CONDITIONS)
        self.assertListEqual(weights, [0, 0, 0])

    def test_that_weights_are_zero_when_conditions_are_missing(self):
        for i in range(5):
            User.objects.create(
                user_id = str(i), consent = True, email = 'test@email.com',
                contact_outcome = False, user_created = timezone.now()
            )
        
        UserCondition.objects.create(
            user = User.objects.get(user_id = '0'),
            condition = 'meta',
            order = 'random'
        )
        UserCondition.objects.create(
            user = User.objects.get(user_id = '1'),
            condition = 'concatenated',
            order = 'random'
        )

        _, weights = get_condition()
        self.assertListEqual(weights, [1, 0, 1])

    def test_that_distribution_of_conditions_is_broadly_equal(self):
        user_bulk = [
            User(
                user_id = str(i), consent = True, email = 'test@email.com',
                contact_outcome = False, user_created = timezone.now()
            )
            for i in range(301)
        ]
        User.objects.bulk_create(user_bulk)

        condition_bulk = [
            UserCondition(
                user = User.objects.get(user_id = str(i)),
                condition = get_condition()[0],
                order = 'random'
            )
            for i in range(301)
        ]

        UserCondition.objects.bulk_create(condition_bulk)

        condition, weights = get_condition()
        print('Condition weights:', weights)

class GetOrderTest(TestCase):

    def test_no_saved_orders(self):
        order, weights = get_order()
        
        self.assertTrue(isinstance(order, str))
        self.assertTrue(order in settings.ORDER)
        self.assertListEqual(weights, [0, 0])
    
    def test_that_weights_are_zero_when_orders_are_missing(self):
        for i in range(5):
            User.objects.create(
                user_id = str(i), consent = True, email = 'test@email.com', 
                contact_outcome = False, user_created = timezone.now()
            )
        
        UserCondition.objects.create(
            user = User.objects.get(user_id = '0'),
            condition = 'meta',
            order = 'random'
        )
        UserCondition.objects.create(
            user = User.objects.get(user_id = '1'),
            condition = 'meta',
            order = 'random'
        )

        _, weights = get_order()
        self.assertListEqual(weights, [2, 0])

    def test_that_distribution_of_conditions_is_broadly_equal(self):
        user_bulk = [
            User(
                user_id = str(i), consent = True, email = 'test@email.com',
                contact_outcome = False, user_created = timezone.now()
            )
            for i in range(301)
        ]
        User.objects.bulk_create(user_bulk)

        condition_bulk = [
            UserCondition(
                user = User.objects.get(user_id = str(i)),
                condition = 'meta',
                order = get_order()[0]
            )
            for i in range(301)
        ]
        UserCondition.objects.bulk_create(condition_bulk)

        order, weights = get_order()
        print('Order weights:', weights)