
import random as rand 
rand.seed(42)

from django.db.models import Count
from django.conf import settings
from museum_site.models import UserCondition

"""
Get the last assignment (either condition or model)
Remove the last assignment from the options (locally)
Randomly select between the remaining option(s)

"""


def _random_selector_conditions_and_order(name = 'condition'):
    if name not in ['condition', 'order']:
        raise ValueError('name has to be either condition or order')
    
    try: 
        last_assignment = UserCondition.objects.latest('timestamp')
        exists = True
    except UserCondition.DoesNotExist:
        exists = False

    is_condition = name == 'condition'

    if exists:
        if is_condition:
            last_assignment = last_assignment.condition
            result = rand.choice([option for option in settings.CONDITIONS if option != last_assignment])
        else:
            last_assignment = last_assignment.order
            result = rand.choice([option for option in settings.ORDER if option != last_assignment])
    else:
        if is_condition:
            result = rand.choice(settings.CONDITIONS)
        else:
            result = rand.choice(settings.ORDER)

    if isinstance(result, list):
        return result[0]
    
    return result


def get_condition():
    return _random_selector_conditions_and_order(name = 'condition')

def get_order():
    return _random_selector_conditions_and_order(name = 'order')