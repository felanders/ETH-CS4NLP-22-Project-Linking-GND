import requests 
import time
from thefuzz import fuzz
from geopy.geocoders import Nominatim

loc = Nominatim(user_agent="GetLoc")

def get_years(data):
    dictionary = {}
    if "dateOfDeath" in data:
        try:
            dictionary["Death Year"] = int(data["dateOfDeath"][0].split("-")[0])
        except:
            dictionary["Death Year"] = 0
    else:
        dictionary["Death Year"] = 0
    if "dateOfBirth" in data:
        try:
            dictionary["Birth Year"] = int(data["dateOfBirth"][0].split("-")[0])
        except:
            dictionary["Birth Year"] = 0
    else:
        dictionary["Birth Year"] = 0
    return dictionary

def get_professions(data):
    dictionary = {"Professions": []}
    if "professionOrOccupation" in data:
        for profession in data["professionOrOccupation"]:
            dictionary["Professions"].append(profession["label"])
    return dictionary

def get_places(data):
    dictionary = {"Places": []}
    if "placeOfDeath" in data:
        for place in data["placeOfDeath"]:
            dictionary["Places"].append(place['label'])
        dictionary["Places"].append(data["placeOfDeath"][0]["label"])
    if "placeOfBirth" in data:
        for place in data["placeOfBirth"]:
            dictionary["Places"].append(place['label'])
    if "placeOfActivity" in data:
        for place in data["placeOfActivity"]:
            dictionary["Places"].append(place["label"])
    if "geographicAreaCode" in data:
        for place in data["geographicAreaCode"]:
            dictionary["Places"].append(place["label"])
    return dictionary

def get_personal_info(data):
    dictionary = {
        "PrefName": [],
        "FirstName": [], 
        "LastName": [],
        "Biography": []
    }
    if "preferredName" in data:
        dictionary["PrefName"].append(data["preferredName"])
    if "preferredNameEntityForThePerson" in data:
        name = data["preferredNameEntityForThePerson"]
        if "forename" in name:
            dictionary["FirstName"].append(name["forename"][0])
        if "surname" in name:
            dictionary["LastName"].append(name["surname"][0])
    if "variantNameEntityForThePerson" in data:
        for name in data["variantNameEntityForThePerson"]:
            if "forename" in name:
                dictionary["FirstName"].append(name["forename"][0])
            if "surname" in name:
                dictionary["LastName"].append(name["surname"][0])
    if "biographicalOrHistoricalInformation" in data:
        dictionary["Biography"].append(data["biographicalOrHistoricalInformation"][0])
    return dictionary

def get_coordinates(location):
    try:
        getLoc = loc.geocode(location)
    except:
        return None
    if getLoc is not None:
        return (getLoc.latitude, getLoc.longitude)
    else:
        return None

def get_coords_from_candidate(candidate):
    d = {"coordinates": []}
    if "Places" in candidate:
        coordinates = []
        for place in candidate["Places"]:
                coordinates.append(get_coordinates(place))
                d["coordinates"] = coordinates
    else:
        d["coordinates"] = []
    return d

def get_coords_from_entity(ent):
    d = {"coordinates": []}
    if "places" in ent:
        coordinates = []
        for place in ent["places"]:
                coordinates.append(get_coordinates(place))
                d["coordinates"] = coordinates
    else:
        d["coordinates"] = []
    return d

def get_gnd_dict(id):
    # If the request times out wait a second and try again
    if id:
        try:
            res = requests.get(f"http://lobid.org/gnd/{id}.json")
        except:
            try:
                time.sleep(1)
                res = requests.get(f"http://lobid.org/gnd/{id}.json")
            except:
                return {}
        try:
            data = res.json()
        except:
            data = False
    else:
        # For id == "" return an "empty candidate" !
        data = {"empty_candidate": True}
    dictionary = {}
    if data:
        dictionary.update(get_personal_info(data))
        dictionary.update(get_places(data))
        dictionary.update(get_professions(data))
        dictionary.update(get_years(data))
        dictionary.update(get_coords_from_candidate(dictionary))
    return dictionary

def create_metagrid_candidates(ent):
    # If the request times out wait a second and try again
    try:
        res = requests.get("https://api.metagrid.ch/search", params={"group": 0, "skip": 0, "take": 150, "provider": "gnd", "query": f"add*{ent['name']}"})
    except:
        try:
            time.sleep(1)
            res = requests.get("https://api.metagrid.ch/search", params={"group": 0, "skip": 0, "take": 150, "provider": "gnd", "query": f"add*{ent['name']}"})
        except:
            return []
    try:
        data = res.json()
    except:
        data = {}
    candidates = []
    partial = []
    intermediate_candidates = []
    if "resources" in data:
        for first in [ent["firstname"]] + ent["abbr_firstname"]:
            first = first.lower()
            for last in [ent["lastname"]]:
                last = last.lower()
                for cand in data["resources"]:
                    first_name = cand["metadata"]["first_name"].lower()
                    last_name = cand["metadata"]["last_name"].lower()
                    full_name = first_name + " " + last_name
                    if fuzz.token_set_ratio(ent["name"], full_name) == 100:
                        intermediate_candidates.append(cand)
                    elif first in first_name and last in last_name:
                        intermediate_candidates.append(cand)
                    if first in first_name and last not in last_name:
                        partial.append(cand)
                    if first not in first_name and last in last_name:
                        partial.append(cand)         
    if len(intermediate_candidates) == 0 and len(partial) > 0:
        intermediate_candidates = partial
    elif len(intermediate_candidates) == 0 and len(partial) == 0:
        intermediate_candidates = []
    for item in intermediate_candidates:
        dictionary = item["metadata"]
        # Remove redundant names
        dictionary.pop("first_name", None)
        dictionary.pop("last_name", None)
        dictionary.update({"Gnd": item["identifier"]})
        dictionary.update(get_gnd_dict(id=dictionary["Gnd"]))
        candidates.append(dictionary)
    # Append the empty candidate
    dictionary = {}
    dictionary.update({"Gnd": ""})
    dictionary.update(get_gnd_dict(id=dictionary["Gnd"]))
    candidates.append(dictionary)
    return candidates