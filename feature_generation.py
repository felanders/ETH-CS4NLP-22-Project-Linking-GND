import haversine as hs
from geopy.geocoders import Nominatim
from gensim.similarities import levenshtein
from gensim.models.fasttext import FastTextKeyedVectors
import numpy as np
from thefuzz import fuzz
from evaluation import label_and_match_to_key
from utils import get_gnd
import regex as re
from candidate_generation import get_coords_from_candidate

loc = Nominatim(user_agent="GetLoc")
ft = FastTextKeyedVectors.load("./fasttext")

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

def compare_gnd_to_label(candidate_gnd, gt_label):
    if candidate_gnd == gt_label:
        match = True
    else:
        match = False
    return label_and_match_to_key(gt_label=gt_label, match=match)

def candidates_to_features(ent, candidates, gt_label):
    y_list = []
    feature_list = []
    for candidate in candidates:
        features = create_features(ent, candidate)
        y_list.append(compare_gnd_to_label(candidate_gnd=get_gnd(candidate), gt_label=gt_label))
        feature_list.append(features)
    return {"features": feature_list, "y": y_list}

def process_fuseki_candidates(candidates):
    """
    fuseki candidates are given to us in the form:
    candidates created via fuseki is a dictionary with key gnd_id and the values are sets.
    example
    116272295
        "x" : {'https://d-nb.info/gn.../116272295'}
        "gid" : {'116272295'}
        "name" : {'b0'}
        "prefForename": {'Otto'}
        "prefSurname": {'Ahrens'}
        "y": {'b1'}
        "varForename": {'O.'}
        "varSurname": {'Ahrens'}
        "job": {'https://d-nb.info/gn.../4044300-0'}
        "activeplace":{'https://d-nb.info/gn.../4749047-0'}
        "activeperiod":{'1897'}
        "desc":{'Verf. von Mecklenburgica'}
        "generalArea":{'https://d-nb.info/st...code#XA-DE'}
    and depending on the info we have even more than this (birthdate, deathdate etc)
    """
    candidate_list = []

    for gnd_id in candidates:
        curr_cand = dict()
        curr_cand["Gnd"] = gnd_id

        curr_cand["PrefName"] = []
        curr_cand["FirstName"] = []
        curr_cand["LastName"] = []

        if "prefForename" in candidates[gnd_id]:
            firstnames_list = list(candidates[gnd_id]["prefForename"])
            curr_cand["FirstName"] += firstnames_list
        if "prefSurname" in candidates[gnd_id]:
            lastnames_list = list(candidates[gnd_id]["prefSurname"])
            curr_cand["LastName"] += lastnames_list
        
        if  "prefForename" in candidates[gnd_id] and "prefSurname" in candidates[gnd_id]:
            curr_cand["PrefName"] = [" ".join(curr_cand["LastName"]) + ", " + " ".join(curr_cand["FirstName"])]
        
        if curr_cand["FirstName"] == []:
            if "varForename" in candidates[gnd_id]:
                varfirstnames_list = list(candidates[gnd_id]["varForename"])
                curr_cand["FirstName"] += varfirstnames_list
        if curr_cand["LastName"] == []:
            if "varSurname" in candidates[gnd_id]:
                varlastnames_list = list(candidates[gnd_id]["varSurname"])
                curr_cand["LastName"] += varlastnames_list
        #we do not set prefName according to the varnames even if we have no prefnames.
        
        #take care of duplicates
        curr_cand["LastName"] = list(set(curr_cand["LastName"]))
        curr_cand["FirstName"] = list(set(curr_cand["FirstName"]))

        curr_cand["Biography"] = []
        if "desc" in candidates[gnd_id]:
            for i in candidates[gnd_id]["desc"]:
                curr_cand["Biography"].append(i)
        
        curr_cand["Places"] = []
        if "activeplace" in candidates[gnd_id]:
            for i in candidates[gnd_id]["activeplace"]:
                activeplace = extract_field_by_gnd("placeOfActivity", i.split("/")[-1], False)
                if activeplace != "":
                    curr_cand["Places"].append(activeplace)
        if "birthplace" in candidates[gnd_id]:
            for i in candidates[gnd_id]["birthplace"]:
                birthplace = extract_field_by_gnd("placeOfBirth", i.split("/")[-1], False)
                if birthplace != "":
                    curr_cand["Places"].append(birthplace)
        if "deathplace" in candidates[gnd_id]:
            for i in candidates[gnd_id]["deathplace"]:
                deathplace = extract_field_by_gnd("placeOfDeath", i.split("/")[-1], False)
                if deathplace != "":
                    curr_cand["Places"] .append(deathplace)
        if "generalArea" in candidates[gnd_id]:
            for i in candidates[gnd_id]["generalArea"]:
                general_area = extract_field_by_gnd("geographicAreaCode", i.split("/")[-1], False)
                if general_area != "":
                    curr_cand["Places"].append(general_area)
        
        curr_cand["Professions"] = []
        if "job" in candidates[gnd_id]:
            for i in candidates[gnd_id]["job"]:
                curr_job = extract_field_by_gnd("professionOrOccupation", i.split("/")[-1], False)
                curr_cand["Professions"].append(curr_job)
        
        curr_cand["Death Year"] = 0
        if "deathdate" in candidates[gnd_id]:
            dates = " ".join(candidates[gnd_id]["deathdate"])
            year_regex = re.findall(r'\d{4}', dates)
            year_regex.sort()
            if (len(year_regex) != 0):
                curr_cand["Death Year"] = int(year_regex[-1])
        curr_cand["Birth Year"] = 0
        if "birthdate" in candidates[gnd_id]:
            dates = " ".join(candidates[gnd_id]["birthdate"])
            year_regex = re.findall(r'\d{4}', dates)
            year_regex.sort()
            if (len(year_regex) != 0):
                curr_cand["Birth Year"] = int(year_regex[0])
                   
        curr_cand.update(get_coords_from_candidate(curr_cand))

        candidate_list.append(curr_cand)
    #and append the empty candidate
    empty_candidate = {'Gnd': '',
                        'PrefName': [],
                        'FirstName': [],
                        'LastName': [],
                        'Biography': [],
                        'Places': [],
                        'Professions': [],
                        'Death Year': 0,
                        'Birth Year': 0,
                        'coordinates': []}
    candidate_list.append(empty_candidate)
    return candidate_list