import os
import sys
import json
import django
import numpy as np
from dotenv import load_dotenv
from uuid import uuid4

from artukreader import artuk_record_parser

# imports for adding data
sys.path.append('museum_webapp')
os.environ['DJANGO_SETTINGS_MODULE'] = 'museum_webapp.settings'
load_dotenv()
django.setup()

from museum_site.models import Artwork


def row_count(file):
    with open(file, newline='') as file_reader:
        file_reader.seek(0)
        return sum(1 for _ in file_reader) - 1


def to_json(coll, delimiter=None):
    if coll is None:
        return
    delimiter = "," if delimiter is None else delimiter
    return json.dumps([e.strip() for e in coll.split(",")])


def check_nan(x):
    return None if x is None or np.isnan(x) else x


def artuk_metadata(file):
    list_meta = list()
    end = row_count(file)
    for idx, meta in enumerate(artuk_record_parser(file)):
        for i in meta.index:
            artwork = Artwork(
                art_id=uuid4().hex,
                collection=meta.loc[i, "Collection Name"],
                classification=meta.loc[i, "Artwork Classification"],
                title=meta.loc[i, 'Artwork Title'],
                medium=to_json(meta.loc[i, "Medium"]),
                artist=meta.loc[i, 'Artist Name'],
                birth_date=check_nan(check_nan(meta.loc[i, "Artist Birth Date"])),
                death_date=check_nan(meta.loc[i, "Artist Death Date"]),
                earliest_date=check_nan(meta.loc[i, "Earliest Date"]),
                latest_date=check_nan(meta.loc[i, "Latest Date"]),
                image_credit=meta.loc[i, "Image Credit"],
                linked_terms=to_json(meta.loc[i, "Linked Terms"]),
                linked_topics=to_json(meta.loc[i, "Linked Topics"]),
                linked_art_terms=meta.loc[i, "Linked Art Terms"],
                img_file=meta.loc[i, "Filename"],
            )
            artwork.save()

        if (idx + 1) % 1000 == 0 or idx >= end:
            print(f"{idx + 1} artworks saved.")
    return list_meta


if __name__ == "__main__":
    csv_metadata = os.path.join("artwork_metadata", "ArtUK_main_sample.csv")
    if len(sys.argv) > 1:
        csv_metadata = sys.argv[1]
    obj = artuk_metadata(csv_metadata)
