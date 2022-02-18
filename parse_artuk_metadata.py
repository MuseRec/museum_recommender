import os
import sys
import json
import django
import numpy as np
from dotenv import load_dotenv
from os.path import splitext

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
        filename = meta["Filename"].values[0]
        artwork = Artwork(
            art_id=splitext(filename)[0],
            collection=meta["Collection Name"].values[0],
            classification=meta["Artwork Classification"].values[0],
            title=meta['Artwork Title'].values[0],
            medium=to_json(meta["Medium"].values[0]),   # may contain multiple values
            artist=to_json(meta['Artist Name'].values[0]),   # may contain multiple values
            birth_date=to_json(meta["Artist Birth Date"].values[0]),   # may contain multiple values
            death_date=to_json(meta["Artist Death Date"].values[0]),   # may contain multiple values
            earliest_date=check_nan(meta["Earliest Date"].values[0]),
            latest_date=check_nan(meta["Latest Date"].values[0]),
            image_credit=meta["Image Credit"].values[0],
            linked_terms=to_json(meta["Linked Terms"].values[0]),   # may contain multiple values
            linked_topics=to_json(meta["Linked Topics"].values[0]),   # may contain multiple values
            linked_art_terms=meta["Linked Art Terms"].values[0],
            img_file=filename,
            img_location=meta["Location"].values[0],
        )
        artwork.save()

        if (idx + 1) % 1000 == 0 or idx >= end:
            # print(f"{idx + 1} artworks saved.")
            print('{} artworks saved.'.format(idx + 1))

    return list_meta


if __name__ == "__main__":
    csv_metadata = os.path.join("artwork_metadata", "ArtUK_main_sample_locations.csv")
    if len(sys.argv) > 1:
        csv_metadata = sys.argv[1]
    obj = artuk_metadata(csv_metadata)
