import haversine as hs
from geopy.geocoders import Nominatim
from gensim.similarities import levenshtein
from gensim.models.fasttext import FastTextKeyedVectors
import numpy as np
from thefuzz import fuzz

loc = Nominatim(user_agent="GetLoc")
ft = FastTextKeyedVectors.load("./fasttext")

def get_gnd(candidate):
        return candidate["Gnd"]

def get_min_distance(pairs):
    distances = []
    for a, b in pairs:
        if a is not None and b is not None:
            distances.append(hs.haversine(a, b))
    if distances:
        return min(distances)
    else:
        # half the equator
        return 20000

def get_place_similarity(mention, candidate):
    pairs = []
    if "coordinates" in mention and mention["coordinates"]:
        coordinates = mention["coordinates"]
        for mention_coord in coordinates:
            if "coordinates" in candidate:
                for candidate_coord in candidate["coordinates"]:
                    pairs.append((mention_coord, candidate_coord))
    return [get_min_distance(pairs=pairs)]


def get_years(mention, candidate):
    year = int(mention["year"])
    result = [year]
    if "Birth Year" in candidate:
        result.append(year - int(candidate["Birth Year"]))
    else:
        result.append(year)
    if "Death Year" in candidate:
        result.append(year - int(candidate["Death Year"]))
    else:
        result.append(year)
    return result

def cosine_sim(a, b):
    similarities = []
    for x in a:
        for y in b:
            similarities.append(ft.distance(x, y))
    if similarities:
        return max(similarities)
    else:
        return 0

def get_profession_similarity(mention, candidate):
    pairs = []
    if 'profession' in mention and mention['profession']:
        for mention_profession in mention["profession"]:
            if "Professions" in candidate:
                for candidate_profession in candidate["Professions"]:
                    pairs.append((mention_profession, candidate_profession))
            if "Biography" in candidate:
                for bio in candidate["Biography"]:
                    pairs.append((mention_profession, bio))
        similarities = []
        for pair in pairs:
            for a in pair[0].split(" "):
                for b in pair[1].split(" "):
                    similarities.append(cosine_sim(
                        a.strip().strip(",").strip(";"), 
                        b.strip().strip(",").strip(";")
                    ))
        if similarities:
            return [max(similarities)]
        else:
            return [0]
    return [0]

def score_name_similarity(pairs):
    score_fun = "fuzz"
    scores = []
    for pair in pairs:
        if score_fun == "fuzz":
            local_scores =[fuzz.ratio(pair[0].lower(), pair[1].lower()), 
            fuzz.partial_ratio(pair[0].lower(), pair[1].lower()), 
            fuzz.token_set_ratio(pair[0].lower(), pair[1].lower()), 
            fuzz.token_sort_ratio(pair[0].lower(), pair[1].lower()),
            fuzz.partial_token_set_ratio(pair[0].lower(), pair[1].lower())]
            scores.append(np.mean(local_scores))
        if score_fun == "levenshtein":
            scores.append(levenshtein.editdist(pair[0], pair[1]))
        if score_fun == "fasttext":
            pass
    if scores:
        if score_fun == "fuzz":
            return max(scores)
        if score_fun == "levenshtein":
            return min(scores)
        if score_fun == "fasttext":
            pass
    else:
        if score_fun == "fuzz":
            return 0
        if score_fun == "levenshtein":
            return 100
        if score_fun == "fasttext":
            pass

def get_name_similarity(mention, candidate):
    pair_scores = []
    # name
    pairs = []
    if "name" in mention and mention["name"]:
        name = mention["name"]
        if "PrefName" in candidate:
            for name_cand in candidate["PrefName"]:
                pairs.append((name, name_cand))
        pair_scores.append(score_name_similarity(pairs))
    else:
        pair_scores.append(0)
    pairs = []
    if "firstname" in mention and mention["firstname"]:
        firstname = mention["firstname"]
        if "FirstName" in candidate:
            for name_cand in candidate["FirstName"]:
                pairs.append((firstname, name_cand))
        pair_scores.append(score_name_similarity(pairs))
    else:
        pair_scores.append(0)
    pairs = []
    if "lastname" in mention and mention["lastname"]:
        lastname = mention["lastname"]
        if "LastName" in candidate:
            for lastname_cand in candidate["LastName"]:
                pairs.append((lastname, lastname_cand))
        pair_scores.append(score_name_similarity(pairs))
    else:
        pair_scores.append(0)
    return pair_scores

def create_features(m, c):
    result = get_name_similarity(m, c) + get_years(m, c) + get_profession_similarity(m, c)
    result += get_place_similarity(m, c)
    return result