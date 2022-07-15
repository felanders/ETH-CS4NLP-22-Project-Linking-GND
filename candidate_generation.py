import requests 
import time
import json
from thefuzz import fuzz
from geopy.geocoders import Nominatim
import SPARQLWrapper
from SPARQLWrapper import JSON, SPARQLExceptions, SPARQLWrapper
import pprint as pp

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
            if dictionary["FirstName"] == []:
                if "forename" in name:
                    dictionary["FirstName"] += name["forename"]
            if dictionary["LastName"] == []:
                if "surname" in name:
                    dictionary["LastName"] += name["surname"][0]
    if "biographicalOrHistoricalInformation" in data:
        dictionary["Biography"].append(data["biographicalOrHistoricalInformation"][0])
    
    dictionary["LastName"] = list(set(dictionary["LastName"]))
    dictionary["FirstName"] = list(set(dictionary["FirstName"]))
    
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
        # Remove redundant keys
        dictionary.pop("first_name", None)
        dictionary.pop("last_name", None)
        dictionary.pop("birth_date", None)
        dictionary.pop("death_date", None)
        dictionary.update({"Gnd": item["identifier"]})
        dictionary.update(get_gnd_dict(id=dictionary["Gnd"]))
        candidates.append(dictionary)
    # Append the empty candidate
    dictionary = {}
    dictionary.update({"Gnd": ""})
    dictionary.update(get_gnd_dict(id=dictionary["Gnd"]))
    candidates.append(dictionary)
    return candidates

    
#### Fuseki Candidate Generation Helpers #####

def remove_obsolete_abbrevs(fnames, abbr_firstname, prep_for_query=True):
    """
    Remove abbreviated firstnames, that are already covered by full firstnames.
    e.g. fnames = ["R.", "Richard"] => fnames = ["Richard"]
    """
    cleaned_abbr_fnames = []
    for abbr_group in abbr_firstname:  # this is now a list
        cleaned_abbr_group = []
        for abbr in abbr_group:
            is_obsolete = False
            abbr = abbr.rstrip(".")
            for fname in fnames:
                if fname.startswith(abbr):
                    is_obsolete = True
            if not is_obsolete:
                if prep_for_query:
                    cleaned_abbr_group.append(abbr + "*")
                else:
                    cleaned_abbr_group.append(abbr + ".")
        cleaned_abbr_fnames.append(cleaned_abbr_group)
    
    return cleaned_abbr_fnames

def get_candidates_fuseki(person):
    """
    Call the RDF library to find candidates.
    This can actually only be used if a Fuseki server is running.
    """
    if len(person["lastname"]) == 0 or (len([c for x in " ".join(person["lastname"]) for c in x]) < 2) or (not person["firstname"] and not person["abbr_firstname"]):
        return {}

    fnames = person["firstname"].split(" ")
    print(fnames)
    #fnames = list(set([x for y in fnames for x in y]))
    abbr_fnames = remove_obsolete_abbrevs(fnames, person["abbr_firstname"])
    abbr_fnames = list(set([x for y in abbr_fnames for x in y if x!="*"]))
    #abbr_fnames = " ".join(abbr_fnames)
    print(abbr_fnames)

    lastname = person["lastname"].split(" ")
    print(lastname)
    if fnames == [""]:
        names = " AND ".join(abbr_fnames + lastname)
    else:
        names = " AND ".join(fnames + abbr_fnames + lastname)
    print(names)
    if(len(lastname) > 1):
        lastname = " ".join(lastname)
    else:
        lastname = lastname[0]
    pref_names_format = lastname + ", " + " ".join(fnames) 
    query_string = """
        PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
        PREFIX text: <http://jena.apache.org/text#>
        SELECT *
        WHERE {{
            {{?x text:query "{0}" . }}
            UNION
            {{?x text:query (gndo:variantNameForThePerson "{0}") . }}
            UNION
            {{?x gndo:preferredNameForThePerson ?s .
            FILTER (?s = "{1}") . }}
            ?x a gndo:DifferentiatedPerson .
            ?x gndo:gndIdentifier ?gid .
            ?x gndo:preferredNameEntityForThePerson ?name .
            OPTIONAL {{ ?name gndo:prefferedNameForThePerson ?prefVarName . }}
            OPTIONAL {{ ?name gndo:forename ?prefForename . }}
            OPTIONAL {{ ?name gndo:prefix ?prefPrefix . }}
            OPTIONAL {{ ?name gndo:surname ?prefSurname . }}
            OPTIONAL {{ ?name gndo:personalName ?prefPersName . }}
            OPTIONAL {{ ?name gndo:nameAddition ?prefNameAddition . }}
            OPTIONAL {{ ?x gndo:variantNameEntityForThePerson ?y . 
                OPTIONAL {{ ?y gndo:variantNameForThePerson ?varName . }}
                OPTIONAL {{ ?y gndo:forename ?varForename . }}
                OPTIONAL {{ ?y gndo:prefix ?varPrefix . }}
                OPTIONAL {{ ?y gndo:surname ?varSurname . }}
                OPTIONAL {{ ?y gndo:personalName ?varPersName . }}
                OPTIONAL {{ ?y gndo:nameAddition ?varNameAddition . }}
            }}
            OPTIONAL {{ ?x gndo:professionOrOccupationAsLiteral ?jobliteral . }}
            OPTIONAL {{ ?x gndo:gndSubjectCategory ?category . }}
            OPTIONAL {{ ?x gndo:academicDegree ?academic . }}
            OPTIONAL {{ ?x gndo:professionOrOccupation ?job . }}
            OPTIONAL {{ ?x gndo:dateOfBirth ?birthdate . }}
            OPTIONAL {{ ?x gndo:dateOfDeath ?deathdate . }}
            OPTIONAL {{ ?x gndo:placeOfBirth ?birthplace . }}
            OPTIONAL {{ ?x gndo:placeOfDeath ?deathplace . }}
            OPTIONAL {{ ?x gndo:placeOfBirthAsLiteral ?birthplaceLiteral . }}
            OPTIONAL {{ ?x gndo:placeOfDeathAsLiteral ?deathplaceLiteral . }}
            OPTIONAL {{ ?x gndo:placeOfActivity ?activeplace . }}
            OPTIONAL {{ ?x gndo:periodOfActivity ?activeperiod . }}
            OPTIONAL {{ ?x gndo:biographicalOrHistoricalInformation ?desc . }}
            OPTIONAL {{ ?x gndo:geographicAreaCode ?generalArea . }}
            OPTIONAL {{ ?x gndo:affiliationAsLiteral ?affiliationLiteral . }}
        }}
        """.format(names, pref_names_format)
    endpoint = SPARQLWrapper("http://localhost:3030/persondata")
    endpoint.setQuery(query_string)
    endpoint.setReturnFormat(JSON)

    try:
        results = endpoint.query().convert()
    except SPARQLExceptions.EndPointInternalError:
        pp.pprint("Invalid query")
        pp.pprint(query_string)
        return {}
    except json.decoder.JSONDecodeError as e:
        pp.pprint(e)
        pp.pprint("Couldn't decode answer!")
        pp.pprint(query_string)
        return {}

    results = results["results"]["bindings"]
    if len(results) == 0:
        print("results is empty")
        print(names)
        return {}
    else:
        print("sucessfully linked")
   
    unique_candidate_dict = {}
    for result in results:
        uid = result["gid"]["value"]
        unique_candidate_dict.setdefault(uid, dict())
        for attname, attvalue in result.items():
            unique_candidate_dict[uid].setdefault(attname,set()).add(attvalue["value"])

    return unique_candidate_dict

def extract_field_by_gnd(field, gnd_id, is_per = False):
    lobid_url = "http://lobid.org/gnd/"+gnd_id+".json"
    try:
        res = requests.get(lobid_url, timeout=5)
    except requests.ReadTimeout:
        return ""
    if (res.status_code != 200):
        return ""
    try:
        lobid_json = json.loads(res.text)
    except ValueError:
        print("this url: "+ lobid_url + " threw a json decode error")
        return ""
    if is_per:
        print(lobid_json.keys())
        field_list = []
        for i in lobid_json[field]:
            field_list.append(i["label"])
        return field_list
    else:
        #profession and place gnds
        return lobid_json["preferredName"]
