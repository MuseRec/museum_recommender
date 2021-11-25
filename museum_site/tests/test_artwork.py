from django.test import TestCase
from django.utils import timezone
from uuid import uuid4

from museum_site.models import Artwork

# python manage.py test museum_site.tests.test_artwork


class ArtworkTest(TestCase):
    sample_record = {
        "art_id": "abf8f1bb509a44f4920406f3d3e1136c",
        "collection": "Faculty of English Language and Literature",
        "classification": "Painting",
        "title": "Gudbrandur Vigfusson",
        "medium": '["acrylic", "plastic", "fibreglass", "wood", "metal & plastic"]',
        "artist": '["Henry Marriott"]',
        "birth_date": '["1856"]',
        "death_date": '["1936"]',
        "earliest_date": 1888,
        "latest_date": 1888,
        "image_credit": "Royal Institution of Cornwall",
        "linked_terms": '["Book", "Button", "Buttons", "Coat", "Collar"]',
        "linked_topics": '["Evening and formal costume", "Everyday costume"]',
        "linked_art_terms": "Pre‐Raphaelitism",
        "img_file": "file.jpg",
    }

    def setUp(self) -> None:
        art_sample = Artwork.objects.create(**self.sample_record)
        art_sample.save()

    def test_write_to_db(self):
        self.assertEqual(Artwork.objects.all().count(), 1)

    def test_reading_from_db(self):
        art_sample = Artwork.objects.get(art_id=self.sample_record["art_id"])
        for k, v in art_sample.__dict__.items():
            if k in self.sample_record:
                self.assertEqual(v, self.sample_record[k])
