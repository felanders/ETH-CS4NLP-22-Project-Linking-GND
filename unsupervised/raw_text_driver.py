"""
Here I calculate the vectors for the input text.
"""

import numpy as np
import os

def get_file_path(file_name, raw_data_path):
    """
    Parse file name to extract magazine name, year and actual file name.

    @return: the file path for that specific file
    """
    magazine = file_name[:3]
    year = file_name[8:12]
    
    return os.path.join(raw_data_path, magazine, year, file_name)

def get_context_vectors(file_name, word2vec, raw_data_path):
    path = get_file_path(file_name=file_name, raw_data_path=raw_data_path)
    with open(path, 'r') as my_file:
        lines = my_file.readlines()

    vectors = []
    total = 0
    skipped = 0
    for line in lines:
        splitted = line.split(' ')
        if len(splitted) == 1:
            continue
        # print('word is', splitted[0])
        try:
            total = total + 1
            vectors.append(word2vec[splitted[0]])
        except KeyError:
            skipped = skipped + 1
    print(f'Number of context vectors from text {total-skipped}/{total}')
    return np.array(vectors)

def get_context_vectors(file_name, location: str, word2vec, raw_data_path, window_size):
    """
    assume the raw text information is: {'page': 'dkm-003_2010_070_0048.txt', 'coords': '1353,2120,113,29'}

    @param file_name: dkm-003_2010_070_0048.txt
    @param location: 1353,2120
    @param word2vec: glove dictionary
    @param raw_data_path: path to search for
    @param window_size: size to calculate the context information
    """

    path = get_file_path(file_name=file_name, raw_data_path=raw_data_path)
    with open(path, 'r') as my_file:
        lines = my_file.readlines()

    vectors = []
    total = 0
    skipped = 0
    # find the location of the target!
    line_indices = []
    for counter, line in enumerate(lines):
        if location in line:
            # from -window_size to +window_size
            for counter2 in range(-window_size, window_size):
                line_indices.append(counter + counter2)

    # only 1 occurence should be present here!
    assert len(line_indices) == 2*window_size + 1
    
    for line_counter in line_indices:
        line = lines[line_counter]
        splitted = line.split(' ')
        if len(splitted) == 1:
            continue
        # print('word is', splitted[0])
        try:
            total = total + 1
            vectors.append(word2vec[splitted[0]])
        except KeyError:
            skipped = skipped + 1
    print(f'Number of context vectors from text {total-skipped}/{total}')
    return np.array(vectors)