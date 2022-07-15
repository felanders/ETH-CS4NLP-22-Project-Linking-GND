import os
import requests
import re
from difflib import SequenceMatcher
import time
# from urllib.request import urlopen
from bs4 import BeautifulSoup

PATH_CONTENT_DIR = 'data/website_content_cache'
SERVER_URL = 'https://d-nb.info/gnd/'
DEFAULT_ID_1 = '118560239'
DEFAULT_ID_2 = '133758982'


def fetch_resource(gnd):
    """Check if the corresponding file exists! If so, use cache on the disk (the file), otherwise fetch it from the server"""
    gnd = str(gnd)
    cache_file = os.path.join(PATH_CONTENT_DIR, gnd)
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as my_file:
            resource = my_file.read()
    else:
        resource = requests.get(SERVER_URL + str(gnd)).content.decode('utf-8')
        with open(cache_file, 'w') as my_file:
            my_file.write(resource)

    return resource

def get_angaben_text(gnd):
    """Return "Weitere Angaben" section of portal.dnb.de database."""
    data = fetch_resource(str(gnd))

    temp = data.content
    temp = temp.decode('utf-8')
    # print(temp)
    temp = temp.split('Weitere Angaben')[1]
    temp = temp.split('<td class=\'yellow\'>')[1]
    temp = temp.split('</td>')[0]
    temp = temp.rstrip()
    temp = temp.lstrip()
    temp = temp.replace('<br/>', ' ')

    return temp

# get_angaben_text('https://d-nb.info/gnd/1078962529')
def get_whole_text(gnd):
    """Return the whole text with a clean content."""
    temp = fetch_resource(str(gnd))

    # temp = clean_common_text(temp, gnd)
    # clean the tags!
    cleanr = re.compile('<.*?>') 
    temp = re.sub(cleanr, '', temp)
    # clean stupid characters
    temp = temp.rstrip()
    temp = temp.lstrip()
    temp = temp.replace('\t', '')

    return temp


def clean_common_text(text, gnd):
    """Remove common text by looking at different ID websites"""
    gnd = str(gnd)
    if gnd == DEFAULT_ID_1:
        other_text = fetch_resource(str(DEFAULT_ID_2))
    else:
        other_text = fetch_resource(str(DEFAULT_ID_1))
    
    # text = 'bir iki uc'
    # other_text = 'bir iki'
    match = SequenceMatcher(None, text, other_text).find_longest_match(0, len(text), 0, len(other_text))
    while match.size > 40:
        # print('current_text:', text)
        # print('match_size', match.size)
        # print(other_text)
        # time.sleep(5.0)
        text = text[:match.a] + text[match.a + match.size:]
        match = SequenceMatcher(None, text, other_text).find_longest_match(0, len(text), 0, len(other_text))
    
    return text

def clean_this_html(text):
    soup = BeautifulSoup(text, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    # print(text)
    return text

def get_cleaned_whole_text(gnd):
    """Return the whole text with a clean content."""
    temp = fetch_resource(str(gnd))
    temp = clean_this_html(temp)

    temp = clean_common_text(temp, gnd)
    # print('cleaned text:')
    # print(temp)
    # asldjasdjslk

    # temp = clean_common_text(temp, gnd)
    # clean the tags!
    cleanr = re.compile('<.*?>') 
    temp = re.sub(cleanr, '', temp)
    # clean stupid characters
    temp = temp.rstrip()
    temp = temp.lstrip()
    temp = temp.replace('\t', '')

    return temp
