from django.test import TestCase

import pyparsing as pp

from museum_site.models import Artwork
from museum_site.views import query_parser, convert_q, squeeze_list


class SearchAndFilterTest(TestCase):
    def setUp(self) -> None:
        # create artwork that can be passed to the front end
        self.artworks = [
            Artwork.objects.create(
                art_id="image_file_1",
                title="Violets",
                medium="acrylic on board",
                artist='["John Cook"]',
            ),
            Artwork.objects.create(
                art_id="image_file_2",
                title="Japanese Landscape",
                medium="mixed media on board",
                artist='["John Cook"]',
            ),
            Artwork.objects.create(
                art_id="image_file_3",
                title="High Force",
                medium="oil on canvas",
                artist='["John Cook"]',
            ),
            Artwork.objects.create(
                art_id="image_file_4",
                title="Monkey",
                medium="oil on metal",
                artist='["John Cook"]',
            ),
            Artwork.objects.create(
                art_id="image_file_5",
                title="Summer Breeze",
                medium="oil on metal",
                artist='["David Jones"]',
            ),
            Artwork.objects.create(
                art_id="image_file_6",
                title="The Elephant and Castle",
                medium="oil on canvas",
                artist='["David Jones"]',
            ),
            Artwork.objects.create(
                art_id="image_file_7",
                title="Sailing Boats at Sea",
                medium="wood, creosote & hinges",
                artist='["David Jones"]',
            ),
            Artwork.objects.create(
                art_id="image_file_8",
                title="Sailing Boats at Sea",
                medium="mixed media on board",
                artist='["Graham Murray"]',
            ),
            Artwork.objects.create(
                art_id="image_file_9",
                title="Landscape with Shepherds",
                medium="oil on wood",
                artist='["Graham Murray"]',
            ),
        ]

    @staticmethod
    def get_artworks(query):
        query_list = query_parser(query).as_list()
        # Test against random sample
        display_in_query = list(
            filter(
                lambda k: len(k) == 2 and k[0].find("display") != -1,
                squeeze_list(query_list)
            )
        )
        if len(display_in_query) > 0:
            n = display_in_query[0][1]
            if n.isnumeric():
                return Artwork.objects.order_by('?')[:int(n)]
            else:
                return Artwork.objects.all()
        q_obj = convert_q(query_list)
        return Artwork.objects.filter(q_obj)

    def test_of_regular_search(self):
        # Artist
        art = SearchAndFilterTest.get_artworks("artist: Cook")
        self.assertEqual(art.count(), 4)
        art = SearchAndFilterTest.get_artworks("artist: jones")
        self.assertEqual(art.count(), 3)
        art = SearchAndFilterTest.get_artworks("artist: Graham")
        self.assertEqual(art.count(), 2)
        # Medium
        art = SearchAndFilterTest.get_artworks("medium: oil")
        self.assertEqual(art.count(), 5)
        art = SearchAndFilterTest.get_artworks("medium: wood")
        self.assertEqual(art.count(), 2)
        # Title
        art = SearchAndFilterTest.get_artworks("title: Japanese")
        self.assertEqual(art.count(), 1)

        # Test of mixed queries:
        art = SearchAndFilterTest.get_artworks("artist: cook & medium: board")
        self.assertEqual(art.count(), 2)
        art = SearchAndFilterTest.get_artworks("artist: cook medium: board")
        self.assertEqual(art.count(), 5)
        art = SearchAndFilterTest.get_artworks("artist: Graham & title: Landscape")
        self.assertEqual(art.count(), 1)

        # Multiple arguments
        art = SearchAndFilterTest.get_artworks("artist: Graham Cook")
        self.assertEqual(art.count(), 6)
        art = SearchAndFilterTest.get_artworks("artist: Graham Jones & medium: metal wood")
        self.assertEqual(art.count(), 3)

    def test_of_no_results(self):
        # Test of no results
        art = SearchAndFilterTest.get_artworks("artist: AAA")
        self.assertEqual(art.count(), 0)
        art = SearchAndFilterTest.get_artworks("artist: jones & artist: cook")
        self.assertEqual(art.count(), 0)
        art = SearchAndFilterTest.get_artworks("artist: Murray & title: Elephant")
        self.assertEqual(art.count(), 0)

    def test_of_incorrect_queries(self):
        # Missing a keyword
        self.assertRaises(
            pp.ParseException,
            SearchAndFilterTest.get_artworks,
            query="missing keywords",
        )

        # Missing argument for a keyword
        self.assertRaises(
            pp.ParseException,
            SearchAndFilterTest.get_artworks,
            query="artist:",
        )

        # Keywords without arguments are ignored
        art = SearchAndFilterTest.get_artworks("artist: cook medium: title:")
        self.assertEqual(art.count(), 4)

    def test_of_random_sample(self):
        # Correct argument for "display: <number>"
        art = SearchAndFilterTest.get_artworks("display: 2")
        self.assertEqual(art.count(), 2)
        # ignore other keywords if display in the query
        art = SearchAndFilterTest.get_artworks("artwork: AAA display: 5")
        self.assertEqual(art.count(), 5)

        # In case of the incorrect argument for "display: <number>"
        # full database is returned
        art = SearchAndFilterTest.get_artworks("display: a")
        self.assertEqual(art.count(), Artwork.objects.all().count())
