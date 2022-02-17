from django.db import models
from museum_site.models import Artwork

# Create your models here.

class DataRepresentation(models.Model):
    source = models.CharField(max_length = 12)

    def __str__(self) -> str:
        return self.source

class Similarities(models.Model):
    art = models.ForeignKey(Artwork,  on_delete = models.CASCADE)
    similar_art = models.ForeignKey(
        Artwork, 
        on_delete = models.CASCADE,
        related_name = 'similiar_art'
    )
    representation = models.ForeignKey(DataRepresentation, on_delete = models.CASCADE)
    score = models.DecimalField(max_digits = 5, decimal_places = 4)

    def __str__(self) -> str:
        return f"{self.art}; {self.similar_art}; {self.score}; {self.representation}"
