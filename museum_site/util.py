
import random as rand 
rand.seed(42)

from django.db.models import Count
from django.conf import settings
from museum_site.models import UserCondition


def _random_selector_conditions_and_order(name = 'condition'):
    if name not in ['condition', 'order']:
        raise ValueError('name has to be either condition or order')
    
    counts = UserCondition.objects.values(name).annotate(
        total = Count(name)
    ).order_by(f"-{name}")

    is_condition = name == 'condition'

    if is_condition:
        weights = [0, 0, 0]
    else:
        weights = [0, 0]

    if not counts:
        if is_condition:
            result = rand.choice(settings.CONDITIONS)
        else:
            result = rand.choice(settings.ORDER)
    else:
        for count_item in counts:
            if is_condition:
                idx = settings.CONDITION_INDEXES[count_item['condition']]
            else:
                idx = settings.ORDER_INDEXES[count_item['order']]

            weights[idx] = count_item['total']
        
        if is_condition:
            result = rand.choices(settings.CONDITIONS, weights = weights)
        else:
            result = rand.choices(settings.ORDER, weights = weights)

    return result, weights

def get_condition():
    return _random_selector_conditions_and_order(name = 'condition')
    # condition_counts = UserCondition.objects.values('condition').annotate(
    #     total = Count('condition')
    # ).order_by('-condition')

    # # if none has been set, then just randomly select from the conditions
    # if not condition_counts:
    #     condition = rand.choice(settings.CONDITIONS)
    #     weights = [0, 0, 0]
    # else:
    #     weights = [0, 0, 0]
    #     for count_item in condition_counts:
    #         idx = settings.CONDITION_INDEXES[count_item['condition']]
    #         weights[idx] = count_item['total']

    #     condition = rand.choices(settings.CONDITIONS, weights = weights)

    # return condition, weights

def get_order():
    return _random_selector_conditions_and_order(name = 'order')