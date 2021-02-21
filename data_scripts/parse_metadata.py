import json 

from glob import glob

def filter_out_errors(metadata):
    missing_iids = set(json.load(open('../artwork_metadata/iids_missing_images.json', 'r')))
    unidentified_images = set(json.load(
        open('../artwork_metadata/iids_unidentified_images.json', 'r')
    ))

    for indx, meta in enumerate(metadata.copy()):
        if meta['iid'] in missing_iids or meta['iid'] in unidentified_images:
            del metadata[indx]
    
    return metadata

def include_urls(metadata):
    def _read_in_individual_files():
        """ Read in the individual raw metadata files """
        data = []
        for f_name in glob('../artwork_metadata/SAAM_[0-9]*.json'):
            # read in the newline separated json file
            with open(f_name, 'r', encoding = 'UTF-8') as f_in:
                for line in f_in:
                    data.append(json.loads(line))

        return data

    raw_metadata = _read_in_individual_files()
    
    # create an index mapping so we can update the existing parsed metadata to include URLs
    iid_metadata_index_mapping = {meta['iid']: idx for idx, meta in enumerate(metadata)}
    for m_data in raw_metadata:
        iid = m_data['id']

        # if the iid is in the mapping dictionary
        if iid in iid_metadata_index_mapping.keys():
            media =  m_data['content']['descriptiveNonRepeating']['online_media']['media'][0]
            url = media['content']
            thumbnail_url = media['thumbnail']
            
            # update the metadata to include the url 
            metadata[iid_metadata_index_mapping[iid]].update({
                'img_url': url, 'thumbnail_url': thumbnail_url
            })

    return metadata

def include_type_and_subtype(metadata):
    for idx, meta in enumerate(metadata.copy()):
        meta_type = meta['type']

        if '-' in meta_type:
            type_split = meta_type.split('-')
            metadata[idx].update({
                'type_main': type_split[0],
                'type_sub': type_split[1]
            })
        else:
            metadata[idx].update({
                'type_main': meta_type,
                'type_sub': None
            })

        # delete the orginal type
        del metadata[idx]['type']

    return metadata 

def date_ranges_to_string(metadata):
    def _create_contiguous_groupings(sorted_date_ranges):
        groupings = []
        previous_date_range = None 
        current_grouping_index = 0
        for d_range in sorted_date_ranges:
            if d_range is None: 
                continue 

            if previous_date_range is None: 
                previous_date_range = d_range

            # if the difference between the two is greater than 10 (gap in activity)
            if int(d_range.split('s')[0]) - int(previous_date_range.split('s')[0]) > 10:
                groupings.append([d_range])
                current_grouping_index += 1
            else:
                if not groupings: # if the array is empty
                    groupings.append([d_range])
                else:
                    groupings[current_grouping_index].append(d_range)
            
            previous_date_range = d_range

        return groupings

    for idx, meta in enumerate(metadata.copy()):
        date_ranges = meta['dateRange']

        if date_ranges is None:
            updated_date_ranges = {'date_range': None}
        else:
            # sort the date ranges (some are out of order)
            date_ranges = sorted(date_ranges)

            # get the grouping nested array
            date_ranges = _create_contiguous_groupings(date_ranges)

            # join each of the sub arrays
            date_ranges = [
                '-'.join(sub_range) if len(sub_range) < 2
                else sub_range[0] + '-' + sub_range[-1]
                for sub_range in date_ranges
            ]

            # join the entire thing
            date_ranges = " + ".join(date_ranges)

            updated_date_ranges = {'date_range': date_ranges}
        
        metadata[idx].update(updated_date_ranges)
        del metadata[idx]['dateRange']
    
    return metadata


def main():
    # get the metadata
    metadata = json.load(open('../artwork_metadata/SAAM_metadata.json', 'r'))

    # filter out those were there are missing images or unidentified images
    metadata = filter_out_errors(metadata)
    
    # get the urls for the artworks
    metadata = include_urls(metadata)

    metadata = include_type_and_subtype(metadata)

    metadata = date_ranges_to_string(metadata)

    

if __name__ == '__main__':
    main()