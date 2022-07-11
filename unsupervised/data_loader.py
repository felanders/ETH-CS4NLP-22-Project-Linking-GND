import json
import os
import pdb
import gensim.downloader
from modules.unsupervised.portal_dnb_driver import get_angaben_text, get_whole_text
import numpy as np
import logging as different_name_for_logging # im always confused by the name and use logging instead of logger
import pickle
from modules.linking_fuseki import get_candidates
import copy

PATH_ENTITY_MAP = 'data/entity_map_lookup.pickle'

different_name_for_logging.basicConfig()
logger = different_name_for_logging.getLogger()
logger.setLevel(different_name_for_logging.DEBUG)

print('Available models:', list(gensim.downloader.info()['models'].keys()))

class DataLoader:
    def __init__(self, agg_data_path: str, raw_data_path: str):
        """
        1. Scan aggregate data directory and find different magazine folders
        2. Scan raw data directory to find names file names

        @param agg_data_path: is the directory path containing json data (output of the aggregation step)
        @param raw_data_path: is the directory path pointing to the raw text data stored as json (for context information!)
        """
        # 1. Scan data directory and find different magazine folders
        logger.debug('Scanning aggregated data and finding entities')
        if os.path.exists(PATH_ENTITY_MAP):
            logger.warning(f'Entity map table found in {PATH_ENTITY_MAP}, skipping parse stage')
            with open(PATH_ENTITY_MAP, 'rb') as data_file:
                self.entity_map = pickle.load(data_file)
        else:
            logger.warning(f'No entity map table found in {PATH_ENTITY_MAP}, parsing all data files using fuseki')
            self.entity_map = []
            for root_dir, directories, files in os.walk(agg_data_path):
                for file in files:
                    with open(os.path.join(root_dir, file), 'r') as current_json_file:
                        current_json_content = json.load(current_json_file)
                    for entity in current_json_content:
                        # Convert the data shape
                        adapter_entity = self._get_adapter_entity(entity)

                        candidates = get_candidates(adapter_entity)
                        if candidates == {}:
                            logger.debug(f'Invalid candidate for entity {adapter_entity}, nothing returned!')
                            continue

                        self.entity_map.append({'entity': entity, 'candidates': candidates})
            
            with open(PATH_ENTITY_MAP, 'wb') as data_file:
                pickle.dump(self.entity_map, data_file)

        # 2. Create raw file mapping
        logger.debug('Scanning raw data and finding relevant raw text for aggregated entries')
        self.raw_data_path = raw_data_path
        self.raw_file_map = {}
        for root_dir, directories, files in os.walk(raw_data_path):
            for file in files:
                assert file not in self.raw_file_map
                self.raw_file_map[file] = os.path.join(root_dir, file)

        # 3. Create other variables/databases
        logger.debug('Loading glove vectors')
        self.glove_vectors = gensim.downloader.load('glove-twitter-25')
    

        

    def __getitem__(self, idx):
        """Create the vector and label"""
        # Create the context word for each candidate!
        logger.debug('Creating context information using dnb database for candidates')
        possible_candidates = self.get_possible_candidates(idx)
        glove_vector_length = len(self.glove_vectors['the'])
        candidate_document_vectors = np.zeros((len(possible_candidates), glove_vector_length))
        candidate_id_list = []
        for counter, candidate in enumerate(possible_candidates):
            angaben_text = get_whole_text(candidate)
            candidate_id_list.append(candidate)
            
            word_vectors = []
            for word in angaben_text:
                try:
                    word_vectors.append(self.glove_vectors[word])
                except KeyError:
                    # maybe this is not in the vocabulary
                    pass
            logger.debug(f'dnb database words are in the vocabulary for {candidate} is {len(word_vectors)}/{len(angaben_text)}')
            # todo -> this is not the correct place to calculate average!
            candidate_document_vectors[counter, :] = np.array(word_vectors).mean(axis=0)
        
        return_entity = copy.copy(self.entity_map[idx]['entity'])
        return_entity.update({'candidates_dnb_context_vectors': candidate_document_vectors})
        return_entity.update({'candidates_id_list': candidate_id_list})
        
        return return_entity

    def __len__(self):
        return len(self.entity_map)

    def get_possible_candidates(self, idx):
        entity = self.entity_map[idx]
        
        return list(entity['candidates'].keys())

    @staticmethod
    def _get_adapter_entity(entity):
        """
        Adapter function, prepare object to use in `get_candidates` function.
        @param entity: input entity
        @return: adapter_entity to be used in `get_candidates` function
        @side effect: entity is modified if some keys are missing such as firstname
        
        The shape of the data is like this when I read from data:
        {
            'firstname': ['Fatih'],
            'lastname': 'Eser',
            'abbr_firstname': [],
            'address': [],
            'titles': [],
            'profession': [],
            'other': [],
            'references': {
                "dkm-001_1941_001_0429.txt": {
                    "pid": null,
                    "refs": [
                        {
                            "sent": 0,
                            "coords": [
                                "1041,295,99,23:main",
                                "1154,296,96,28:main",
                                "1264,296,81,22:main"
                            ]
                        }
                    ],
                    "elements": []
                }
            },
            "type": "PER",
            "id": 32
        }
        """
        # For some reason `get_candidates` function requires 2 dimensional input array for two entries, `firstname` and `abbr_firstname`
        """The shape required is something like:
        {
            ...
            'firstname': [['Fatih']],
            'abbr_firstname': [[]],
            ...
        }
        """
        if 'firstname' not in entity:
            entity['firstname'] = []
        if 'abbr_firstname' not in entity:
            entity['abbr_firstname'] = []
        if 'lastname' not in entity:
            entity['lastname'] = ''
        
        adapter_entity = copy.copy(entity)
        adapter_entity['firstname'] = [adapter_entity['firstname']]
        adapter_entity['abbr_firstname'] = [adapter_entity['abbr_firstname']]
        adapter_entity['lastname'] = [adapter_entity['lastname']]

        return adapter_entity