from django.shortcuts import render
from django.conf import settings 

from .models import Similarities, DataRepresentation

def get_top_n(artwork, n = 5):
    result_set = Similarities.objects.filter(
        representation = DataRepresentation.objects.get(settings.DATA_REP_TYPE)
    ).get(
        art = artwork
    )

    return result_set
