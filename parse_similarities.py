import pandas as pd 
import os 
import sys 
import json as j 

from dotenv import load_dotenv

load_dotenv()
sys.path.append('/museum_webapp')
os.environ['DJANGO_SETTINGS_MODULE'] = 'museum_webapp.settings'

import django 
django.setup()

from museum_site.models import Artwork
from recommendations.models import Similarities, DataRepresentation

from django.core.exceptions import ObjectDoesNotExist

def write_data_representations():
    for rep in ['meta', 'image', 'concat']:
        dp = DataRepresentation(source = rep)
        dp.save()

def determine_missing_image(img, sim_img):
    try: # is it the main image?
        a = Artwork.objects.get(art_id = img)
    except ObjectDoesNotExist:
        return (img, 'img')

    try: # is it the similar image?
        a = Artwork.objects.get(art_id = sim_img)
    except ObjectDoesNotExist:
        return (sim_img, 'sim_img')

def write_to_similarities_db(file_name):
    data = pd.read_csv('models/' + file_name).to_dict(orient = 'records')
    
    missing_images = []
    bulk = []
    for idx, datum in enumerate(data):
        try: 
            sim = Similarities(
                art = Artwork.objects.get(art_id = datum['img']),
                similar_art = Artwork.objects.get(art_id = datum['sim_img']),
                representation = DataRepresentation.objects.get(source = datum['data_rep']),
                score = datum['score']
            )
            bulk.append(sim)
        except ObjectDoesNotExist:
            # we know that one of the artworks is missing from the database for some reason
            missing_images.append(determine_missing_image(datum['img'], datum['sim_img']))

        if idx % 25000 == 0 and idx != 0:
            # save in a batch and reset the list
            # Similarities.objects.bulk_create(bulk)
            bulk = []

            print(f"{idx} similarities saved")

    return missing_images
    

def main():
    # write the representations to the database
    # write_data_representations()

    """
        There is an issue with missing ID's in the database and it's not clear
        as to why. This is something that needs revisiting for the user study.
    """

    csv_files = [
        'meta_similarties.csv', 
        'image_similarities.csv', 
        'concatenated_similarities.csv'
    ]

    # missing_images = []
    # for f_name in csv_files[:1]:
    #     print(f"Parsing {f_name}...")
    #     missing = write_to_similarities_db(f_name)
    #     missing_images += missing

    
    # print(len(set(missing_images)))

    # print(f"Total number missing: {len(missing_images)}")
    # with open('models/missing_images.json', 'w') as f:
    #     j.dump(missing_images, f)

    # with open('models/missing_images.json', 'r') as f:
    #     missing = j.load(f)
    
    # i = []
    # for img in missing:
    #     try:
    #         i.append(img[0])
    #     except TypeError:
    #         print(img)
    #         exit()
    
    # ids = set([img for img, _ in missing_images])
    # print('Total number of missing ids: ', len(ids))
    

if __name__ == '__main__':
    main()
