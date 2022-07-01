from html import entities
import os
import json
from collections import Counter
from itertools import chain
from collections import defaultdict

#TODO make this a csv or txt file and read it in.
context_pages = ["sbz-002_1895_025_0665.txt","sbz-002_1895_025_0666.txt",
"sbz-002_1895_025_0667.txt","sbz-002_1895_025_0668.txt","sbz-002_1895_025_0669.txt",
"sbz-002_1895_025_0670.txt","sbz-002_1895_025_0671.txt","sbz-002_1895_025_0672.txt",
"sbz-002_1895_025_0673.txt","sbz-002_1895_025_0674.txt","sbz-002_1895_025_0684.txt",
"sbz-002_1895_025_0685.txt","sbz-002_1895_025_0686.txt","sbz-002_1895_025_0687.txt",
"sbz-002_1895_025_0688.txt","sbz-002_1895_025_0689.txt","sbz-002_1895_025_0690.txt",
"sbz-002_1895_025_0691.txt","sbz-002_1895_025_0692.txt","sbz-002_1895_025_0693.txt",
"sbz-002_1940_115_0203.txt","sbz-002_1940_115_0204.txt","sbz-002_1940_115_0205.txt",
"sbz-002_1940_115_0206.txt","sbz-002_1940_115_0207.txt","sbz-002_1940_115_0208.txt",
"sbz-002_1940_115_0209.txt","sbz-002_1940_115_0210.txt","sbz-002_1940_115_0211.txt",
"sbz-002_1940_115_0212.txt","sbz-002_1940_115_0225.txt","sbz-002_1940_115_0226.txt",
"sbz-002_1940_115_0227.txt","sbz-002_1940_115_0228.txt","sbz-002_1940_115_0229.txt",
"sbz-002_1940_115_0230.txt","sbz-002_1940_115_0231.txt","sbz-002_1940_115_0232.txt",
"sbz-002_1940_115_0233.txt","sbz-002_1940_115_0234.txt","sbz-002_1965_083_3162.txt",
"sbz-002_1965_083_3163.txt","sbz-002_1965_083_3164.txt","sbz-002_1965_083_3165.txt",
"sbz-002_1965_083_3166.txt","sbz-002_1965_083_3189.txt","sbz-002_1965_083_3190.txt",
"sbz-002_1965_083_3191.txt","sbz-003_1990_108_1783.txt","sbz-003_1990_108_1784.txt",
"sbz-003_1990_108_1785.txt","sbz-003_1990_108_1786.txt","sbz-003_1990_108_1787.txt",
"sbz-003_1990_108_1788.txt","sbz-003_1990_108_1789.txt","sbz-003_1990_108_1790.txt",
"sbz-003_1990_108_1791.txt","sbz-003_1990_108_1792.txt","sbz-003_1990_108_1802.txt",
"sbz-003_1990_108_1803.txt","sbz-003_1990_108_1804.txt","sbz-003_1990_108_1805.txt",
"sbz-003_1990_108_1806.txt","sbz-003_1990_108_1807.txt","sbz-003_1990_108_1808.txt",
"sbz-003_1990_108_1809.txt","sbz-003_1990_108_1810.txt","sbz-003_1990_108_1811.txt",
"sbz-004_2010_136_0873.txt","sbz-004_2010_136_0874.txt","sbz-004_2010_136_0875.txt",
"sbz-004_2010_136_0876.txt","sbz-004_2010_136_0877.txt","sbz-004_2010_136_0898.txt",
"sbz-004_2010_136_0899.txt","sbz-004_2010_136_0900.txt","sbz-004_2010_136_0901.txt",
"sbz-004_2010_136_0902.txt","dkm-001_1941_001_0418.txt","dkm-001_1941_001_0419.txt",
"dkm-001_1941_001_0420.txt","dkm-001_1941_001_0421.txt","dkm-001_1941_001_0422.txt",
"dkm-001_1941_001_0444.txt","dkm-001_1941_001_0445.txt","dkm-001_1941_001_0446.txt",
"dkm-001_1941_001_0447.txt","dkm-001_1941_001_0448.txt","dkm-001_1941_001_0449.txt",
"dkm-003_1990_050_0375.txt","dkm-003_1990_050_0376.txt","dkm-003_1990_050_0377.txt",
"dkm-003_1990_050_0378.txt","dkm-003_1990_050_0379.txt","dkm-003_1990_050_0401.txt",
"dkm-003_1990_050_0402.txt","dkm-003_1990_050_0403.txt","dkm-003_1990_050_0404.txt",
"dkm-003_1990_050_0405.txt","dkm-003_2010_070_0035.txt","dkm-003_2010_070_0036.txt",
"dkm-003_2010_070_0037.txt","dkm-003_2010_070_0038.txt","dkm-003_2010_070_0039.txt",
"dkm-003_2010_070_0060.txt","dkm-003_2010_070_0061.txt","dkm-003_2010_070_0062.txt",
"dkm-003_2010_070_0063.txt","dkm-003_2010_070_0064.txt"]

#problematic_ref = ["dkm-003_1990_050_0396.txt349,2205,129,24"] #not relevant for this project
class Paths:
    def __init__(self, conf):
        if "PATH_TO_GROUND_TRUTH" in conf and "PATH_TO_OUTFILE_FOLDER" in conf:
            self.paths = {
                "gt": conf["PATH_TO_GROUND_TRUTH"], 
                "link": os.path.join(conf["PATH_TO_OUTFILE_FOLDER"], "link"),
                "eval": os.path.join(conf["PATH_TO_OUTFILE_FOLDER"], "eval"),
                "input": conf["PATH_TO_INPUT_FOLDER"],
            }
            self.state = {
                "magazine": "",
                "file": ""
            }
            self.success = True
        else:
            self.success = False
    
    def update(self, key, value):
        self.state[key] = value

    def get(self, type, key):
        if key == "magazine":
            return os.path.join(self.paths[type], self.state["magazine"])
        elif key == "file":
            return os.path.join(self.paths[type], self.state["magazine"], self.state["file"])
        else:
            return os.path.join(self.paths[type])
    
    def get_json(self, type, key):
        path = self.get(type=type, key=key)
        with open(path, "r") as f:
            content = json.load(f)
        return content
    
    def get_page_list(self, type, key):
        path = str(self.get(type=type, key=key)).replace(".json", "")
        if os.path.exists(path):
            return os.listdir(path)
        else:
            return []

    def check_and_create(self, type, key):
        # TODO potentially clean this up!!!
        if key == "file":
            path = self.get(type=type, key="file")
            if os.path.exists(os.path.dirname(path)):
                return path
            else:
                path = os.path.dirname(path)
        else:
            path = self.get(type=type, key = key)
            if os.path.exists(path):
                return path
        split = path.split("/")
        curr_path = ""
        for i in range(len(split)):
            curr_path = os.path.join(curr_path, split[i])
            if os.path.isdir(curr_path):
                pass
            else:
                os.mkdir(curr_path)
        if key == "file":
            path = self.get(type=type, key="file")
        return path

    def save_json(self, type, key, doc):
        if key == "file":
            with open(self.check_and_create(type=type, key=key), "w") as f:
                json.dump(doc, f)
        else:
            with open(self.check_and_create(type=type, key=key) + ".json", "w") as f:
                json.dump(doc, f)

class Scores:
    def __init__(self, counts_dict={"tp": 0, "fp": 0, "fn": 0, "tn": 0}):
        self.counter = Counter(counts_dict)
        self.precision = 0
        self.recall = 0
        self.f1 = 0

    def compute_scores(self):
        self.precision = self.counter["tp"]/(self.counter["tp"] + self.counter["fp"]) if self.counter["tp"] + self.counter["fp"] != 0 else 0
        self.recall = self.counter["tp"]/(self.counter["tp"] + self.counter["fn"]) if self.counter["tp"] + self.counter["fn"] != 0 else 0
        self.f1 = 2 * self.counter["tp"]/(2*self.counter["tp"] + self.counter["fp"] + self.counter["fn"]) if self.counter["tp"] + self.counter["fp"] + self.counter["fn"] != 0 else 0
        self.accuracy = (self.counter["tp"]+self.counter["tn"])/(self.counter["tp"]+self.counter["tn"]+self.counter["fp"]+self.counter["fn"]) if (self.counter["tp"]+self.counter["tn"]+self.counter["fp"]+self.counter["fn"])!= 0 else 0

    def update_counter(self, counts_dict):
        self.counter.update(counts_dict)

    def get_score(self, round_to=3):
        self.compute_scores()
        result = {
            "tp": self.counter["tp"],
            "fp": self.counter["fp"],
            "fn": self.counter["fn"],
            "tn": self.counter["tn"],
            "Precision": round(self.precision,round_to),
            "Recall": round(self.recall, round_to),
            "F1": round(self.f1, round_to),
            "Accuracy": round(self.accuracy, round_to)
        }
        return result

""" none of this is relevant for the project
def flatten_linked_dict(linked_dict):
    linked_gnd_dict = {}
    for ent in linked_dict:
        if "gnd_ids" in ent and ent["gnd_ids"] and 'type' in ent and ent['type'] == 'PER':
            ref_list = []
            for key in ent["references"]:
                if key in context_pages: continue

                normalized_coords = set()
                for coords in ent["references"][key][0]["coords"]:
                    #clean them up first
                    coords_clean = str(coords).split(":")[0]
                    normalized_coords.add(coords_clean) 
                    coords_clean = str(coords_clean).split(";")
                    for i in coords_clean:
                        normalized_coords.add(i) 
                    #this is because sometimes the same coord could be present but with different suffixes so
                    # "1294,473,237,23:main","1294,473,237,23:rpunc" for example

                for coords in normalized_coords:    
                    ref_list.append({"page": key, "coord": coords, "uniqueid":  key+coords})
                
            for gnd_candidate in ent["gnd_ids"]:
                if ref_list:
                    linked_gnd_dict.setdefault(gnd_candidate,[]).extend(ref_list)
    return linked_gnd_dict

def flatten_gt_dict(gt_dict, pages):
    gt_gnd_dict = {}
    for ent in gt_dict:
        if 'type' in ent and ent['type'] == 'PER' and ent["Gnd"]:
            # flatten the list of references for easier looping
            ref_list = []
            for ref in tuple(chain.from_iterable(ent["references"])):
                if ref["page"] in pages and ref["page"] not in context_pages:
                    ref_list.append({"page": ref["page"], "coord": ref['coord'], "uniqueid": ref["page"] + ref['coord']})
            if ref_list:
                gt_gnd_dict.setdefault(ent["Gnd"], []).extend(ref_list)
            #GT will always have just one candidate
    return gt_gnd_dict

def agg_by_ref_linked(linked_dict):
    ref_dict = dict()

    for ent in linked_dict:
        if "gnd_ids" in ent and ent["gnd_ids"] and 'type' in ent and ent['type'] == 'PER':
            for page in ent["references"]:
                if page in context_pages: 
                    continue

                for refs in ent["references"][page]:
                    normalized_coords = set()
                    coords_list = refs["coords"]
                    for coords in coords_list:
                        coords_clean = str(coords).split(":")[0]
                        coords_clean = str(coords_clean).split(";")
                        for i in coords_clean:
                            normalized_coords.add(i) 
                        #this is because sometimes the same coord could be present but with different suffixes so
                        # "1294,473,237,23:main","1294,473,237,23:rpunc" for example

                    for coords in normalized_coords:
                        uniqueid_key = page+coords
                        value = {"page": page, "coord": coords, "gnds": ent["gnd_ids"]}
                        if ent["gnd_ids"] != []:
                            if uniqueid_key in ref_dict:
                                print("Why is this uniqueid already in the dictionary? "+ str(uniqueid_key))
                            else:
                                ref_dict.setdefault(uniqueid_key,value)
    return ref_dict

def agg_by_ref_gt(gt_dict):
    ref_dict = dict()

    for ent in gt_dict:
        if 'type' in ent and ent['type'] == 'PER' and ent["Gnd"]:
            gnd_id = ent["Gnd"]
            for ref in tuple(chain.from_iterable(ent["references"])):
                if ref["page"] not in context_pages:

                    value = {"page": ref["page"], "coord": ref['coord'], "gnd": gnd_id}
                    uniqueid_key = ref["page"] + ref['coord']
                    if gnd_id != "":
                        if uniqueid_key in ref_dict:
                            print("Why is this uniqueid already in the dictionary? "+ str(uniqueid_key))
                        else:
                            ref_dict.setdefault(uniqueid_key,value)
    return ref_dict

def get_all_refs_gt(gt_dict):
    all_refs_gt = []
    for ent in gt_dict:
        if 'type' in ent and ent['type'] == 'PER':
            for ref in tuple(chain.from_iterable(ent["references"])):
                if ref["page"] not in context_pages:
                    uniqueid_key = ref["page"] + ref['coord']
                    if(uniqueid_key in problematic_ref):
                        continue
                    if uniqueid_key in all_refs_gt:
                        problematic_ref.append(uniqueid_key) #mistake in the GT data
                        continue
                    all_refs_gt.append(uniqueid_key)

    assert(len(set(all_refs_gt)) == len(all_refs_gt))
    return all_refs_gt

def get_all_refs_linked(linked_dict):
    all_refs_linked = []
    for ent in linked_dict:
        if 'type' in ent and ent['type'] == 'PER':
            for page in ent["references"]:
                if page not in context_pages: 
                    for refs in ent["references"][page]:
                        normalized_coords = set()
                        coords_list = refs["coords"]
                        for coords in coords_list:
                            coords_clean = str(coords).split(":")[0]
                            coords_clean = str(coords_clean).split(";")
                            for i in coords_clean:
                                normalized_coords.add(i) 
                            #this is because sometimes the same coord could be present but with different suffixes so
                            # "1294,473,237,23:main","1294,473,237,23:rpunc" for example

                        for coords in normalized_coords:
                            uniqueid_key = page+coords
                            if uniqueid_key in problematic_ref:
                                continue
                            if uniqueid_key in all_refs_linked:
                                problematic_ref.append(uniqueid_key)
                                continue
                            all_refs_linked.append(uniqueid_key)

    assert(len(set(all_refs_linked)) == len(all_refs_linked))
    return all_refs_linked

def eval_references(gt, linked, references_counter):
    #TODO re-introduce the duplicates so we can compare to the new system
    #or exclude them entirely so we can compare to the new system
    #either way this stuff needs to be re-written... tomorrow.
    
    #deal with inconsistent gt data
    all_refs_gt = get_all_refs_gt(gt)
    all_refs_linked = get_all_refs_linked(linked)
    all_valid_refs = set(all_refs_gt).intersection(all_refs_linked)
    
    
    #aggregate by reference, only for entries with a gndid:
    ref_dict_gt = (agg_by_ref_gt(gt))
    ref_dict_linked = (agg_by_ref_linked(linked))

    #sanity checks:
    all_positives = all_valid_refs.intersection(ref_dict_gt)
    print(len(all_positives))
    
    #sanity check
    visited_linked = dict()
    for i in ref_dict_linked:
        visited_linked.setdefault(i,False)

    #sanity check
    visited_gt = dict()
    for i in ref_dict_gt:
        visited_gt.setdefault(i,False)

    #sanity check
    visited_pos = dict()
    for i in all_positives:
        visited_pos.setdefault(i,False)

    for uniqueid in ref_dict_gt:
        if uniqueid not in all_valid_refs:
            continue
        if uniqueid in ref_dict_linked:
            gt_gnd = ref_dict_gt[uniqueid]["gnd"]
            linked_gnds = ref_dict_linked[uniqueid]["gnds"]
            if gt_gnd in linked_gnds:
                assert(visited_linked[uniqueid] == False)
                visited_linked[uniqueid] = True

                references_counter["tp"] += 1

                assert(visited_pos[uniqueid] == False)
                visited_pos[uniqueid] = True
            else:
                assert(visited_linked[uniqueid] == False)
                visited_linked[uniqueid] = True

                references_counter["fn"] += 1

                assert(visited_pos[uniqueid] == False)
                visited_pos[uniqueid] = True
        if uniqueid not in ref_dict_linked:

            references_counter["fn"] += 1

            assert(visited_pos[uniqueid] == False)
            visited_pos[uniqueid] = True

    for uniqueid in ref_dict_linked:
        if uniqueid not in all_valid_refs:
            continue
        if visited_linked[uniqueid] == False:
            references_counter["fp"] += 1
            
    #sanity check
    for i in visited_pos:
        if not visited_pos[i]:
            print(i in ref_dict_gt)
            print(i in ref_dict_linked)
            print(i in all_valid_refs)

    return references_counter


def agg_by_ent_gt(gt_dict):
    ent_dict = dict()
    for ent in gt_dict:
        if 'type' in ent and ent['type'] == 'PER' and ent["Gnd"]:
            # flatten the list of references for easier looping
            refs_list = []
            for ref in tuple(chain.from_iterable(ent["references"])):
                if ref["page"] not in context_pages:
                    refs_list.append({"page": ref["page"], "coord": ref['coord'], "uniqueid":ref["page"] + ref['coord']})
            if refs_list:
                ent_dict.setdefault(ent["Gnd"], refs_list)
    return ent_dict

def create_ent_to_uniqueids_dict(linked_dict):
    ent_to_uniqueids_dict = dict()
    ent_id = 0
    for ent in linked_dict:
        if "gnd_ids" in ent and 'type' in ent and ent['type'] == 'PER':
            for page in ent["references"]:
                if page in context_pages: 
                    continue
                for refs in ent["references"][page]:
                    normalized_coords = set()
                    coords_list = refs["coords"]
                    for coords in coords_list:
                        coords_clean = str(coords).split(":")[0]
                        coords_clean = str(coords_clean).split(";")
                        for i in coords_clean:
                            normalized_coords.add(i) 
                        #this is because sometimes the same coord could be present but with different suffixes so
                        # "1294,473,237,23:main","1294,473,237,23:rpunc" for example

                    for coords in normalized_coords:
                        value = {"gnds": ent["gnd_ids"], "uniqueids":[page+coords]}
                        #if ent["gnd_ids"] != []:
                        if ent_id in ent_to_uniqueids_dict:
                            ent_to_uniqueids_dict[ent_id]["uniqueids"].append(page+coords)
                        else: 
                            ent_to_uniqueids_dict.setdefault(ent_id,value)
                        #else:
            ent_id += 1
    return ent_to_uniqueids_dict

def eval_entities(gt,linked, entities_counter):
    #deal with inconsistent gt data
    all_refs_gt = get_all_refs_gt(gt)
    all_refs_linked = get_all_refs_linked(linked)
    all_valid_refs = set(all_refs_gt).intersection(all_refs_linked)
    
    ent_dict_gt = agg_by_ent_gt(gt)
    ent_dict_linked = create_ent_to_uniqueids_dict(linked)

    #TODO write this again, prettier. 
    for gnd_id in ent_dict_gt:
        refs = ent_dict_gt[gnd_id]
        for ref in refs:
            uniqueid = ref["uniqueid"]
            if uniqueid not in all_valid_refs:
                continue
            for ent in ent_dict_linked:
                if uniqueid in ent_dict_linked[ent]["uniqueids"]:
                    ent_dict_linked[ent].setdefault("gt_gndid",[]).append(gnd_id)
    for uniqueid in all_refs_gt:
        if uniqueid not in all_valid_refs:
            continue
        for ent in ent_dict_linked:
            already_has_gnd = False
            for gnd_id in ent_dict_gt:
                for ref in ent_dict_gt[gnd_id]:
                    if uniqueid in ref["uniqueid"]:
                        already_has_gnd = True
                        break
                if already_has_gnd:
                    break
            if not already_has_gnd and uniqueid in ent_dict_linked[ent]["uniqueids"]:
                ent_dict_linked[ent].setdefault("gt_gndid",[]).append("")
  
    #sanity check
    mistakes_count = 0
    for ent in ent_dict_linked:
        if "gt_gndid" in ent_dict_linked[ent] and len(set(ent_dict_linked[ent]["gt_gndid"]))>1:
            mistakes_count += 1
            #print(set(ent_dict_linked[ent]["gt_gndid"]))
    #print("ACHTUNG")
    #print(mistakes_count)
    #sanity checks
    visited_linked = dict()
    visited_gt = dict()
    for i in ent_dict_linked.keys():
        visited_linked.setdefault(i, False)
    for i in ent_dict_gt.keys():
        visited_gt.setdefault(i, False)

    for ent in ent_dict_linked:
        #if visited_linked[ent]:
        #    continue
        not_valid = True
        if "gt_gndid" not in ent_dict_linked[ent]:
            for uniqueid in ent_dict_linked[ent]["uniqueids"]:
                if uniqueid in all_valid_refs:
                    not_valid = False
        if not_valid:
            continue
        if len(set(ent_dict_linked[ent]["gt_gndid"]))>1:
            #treat it as if we have len(set(ent_dict_linked[ent]["gt_gndid"]))
            #entities, each with a different gt_gndid and count them seperately
            for gt_gndid in ent_dict_linked[ent]["gt_gndid"]:
                if gt_gndid in ent_dict_linked[ent]["gnds"]:
                    entities_counter["tp"] += 1
                elif ent_dict_linked[ent]["gnds"] == []:
                    entities_counter["fn"] += 1
                else:
                    entities_counter["fp"] += 1
                visited_gt[gt_gndid] = True
            visited_linked[ent] = True
        else:
            gnd_id_gt = set(ent_dict_linked[ent]["gt_gndid"]).pop()
            if gnd_id_gt in ent_dict_linked[ent]["gnds"]:
                entities_counter["tp"] += 1
            elif ent_dict_linked[ent]["gnds"] == []:
                entities_counter["fn"] += 1
            else:
                entities_counter["fp"] += 1
            visited_linked[ent] = True
            visited_gt[gnd_id_gt] = True

    #and now i still need to count the rest of the fp :
    for i in visited_linked:
        if not visited_linked[i]:
            if ent_dict_linked[i]["gnds"] != []:
                entities_counter["fp"] += 1
    #and the rest of the fn because i don't think the line above counts them correctly:
    for i in visited_gt:
        if not visited_gt[i]:
            entities_counter["fn"] += 1
    return entities_counter
"""
# NOTE these are the same functions which we have in "preprocess.py" for our ML solution
# so we can compare the results, we must process the data in the same way
def clean_raw(raw):
    result = []
    for ent in raw:
        if "type" in ent and ent["type"] == "PER":
            ent_mentions = []
            dictionary = {}
            if "lastname" in ent:
                dictionary["lastname"] = ent["lastname"]
            else:
                dictionary["lastname"] = ""
            if "firstname" in ent and ent["firstname"]:
                dictionary["firstname"] = " ".join(ent["firstname"])
            else:
                dictionary["firstname"] = ""
            if "abbr_firstname" in ent:
                dictionary["abbr_firstname"] = ent["abbr_firstname"]
            else:
                dictionary["abbr_firstname"] = []
            if "other" in ent:
                dictionary["other"] = ent["other"]
            else:
                dictionary["other"] = []
            dictionary["name"] = get_main_name(dictionary=dictionary)
            if "profession" in ent:
                dictionary["profession"] = ent["profession"]
            else:
                dictionary["profession"] = []
            places = []
            if "places" in ent:
                for place in ent["places"]:
                    if "name" in place:
                        places.append(place["name"])
            else:
                dictionary["places"] = []
            dictionary["places"] = places
            
            #### new ####
            dictionary["gnd_candidates"] = []
            if "gnd_ids" in ent:
                dictionary["gnd_candidates"] = ent["gnd_ids"]
            #### end new ####

            if "references" in ent:
                for page, refs in ent["references"].items():
                    dictionary.update({
                        "page": page,
                        "year": page.split("_")[1]
                    })
                    for ref in refs:
                        if "coords" in ref:
                            normalized_coords = set()
                            for coord in ref["coords"]:
                                
                                coord_clean = str(coord).split(":")[0]
                                coord_clean = str(coord_clean).split(";")
                                for i in coord_clean:
                                    normalized_coords.add(i) 
                                    
                            for coord in normalized_coords:
                                aux = dictionary.copy()
                                aux.update({"coord": coord})
                                ent_mentions.append(aux)
            

            result.append(ent_mentions)
    return result

def get_main_name(dictionary):
    if "lastname" in dictionary and dictionary["lastname"]:
        if "firstname" in dictionary and dictionary["firstname"]:
            return dictionary["firstname"] + " " + dictionary["lastname"]
        elif "abbr_firstname" in dictionary and dictionary["abbr_firstname"]:
            return " ".join(dictionary["abbr_firstname"]) + " " + dictionary["lastname"]
    elif "firstname" in dictionary and dictionary["firstname"]:
        if "abbr_firstname" in dictionary and dictionary["abbr_firstname"]:
            return dictionary["firstname"] + " " + " ".join(dictionary["abbr_firstname"])
    elif "abbr_firstname" in dictionary and dictionary["abbr_firstname"]:
        return " ".join(dictionary["abbr_firstname"])
    elif "other" in dictionary:
        for l in dictionary["other"]:
            return " ".join(l)
    else:
        return "--"

def clean_gt(gt):
    result = []
    for ent in gt:
        if "type" in ent and ent["type"] == "PER":
            references = ent["references"]
            del ent["references"]
            for ref_list in references:
                for ref in ref_list:
                    aux = ent.copy()
                    aux.update(ref)
                    result.append(aux)
    return result

def label_entity(ent, gt):
    page = ent["page"]
    coord = ent["coord"]
    for g in gt:
        if g["page"] == page:
            if g["coord"] == coord:
                return g["Gnd"]
    return ""

def label_and_match_to_key(gt_label, match):
    if match:
        if gt_label == "":
            return "tn"
        else:
            return "tp"
    else:
        if gt_label == "":
            return "fp"
        else:
           return "fn"

def eval_entity(entity):
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    
    if entity["label"] in [y for x in entity["candidates"] for y in x]:
        key = label_and_match_to_key(gt_label=entity["label"], match=True)
    else:
        key = label_and_match_to_key(gt_label=entity["label"], match=False)
    counts[key] += 1
    
    return counts

def eval_mentions(entity):
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}

    for i,label in enumerate(entity["labels"]):
        if label in entity["candidates"][i]: #TODO maybe undo this specific way of saving candidates idk
            key = label_and_match_to_key(gt_label=label, match=True)
        else:
            key = label_and_match_to_key(gt_label=label, match=False)
        counts[key] += 1

    return counts

def evaluate_person(gt,linked,pages):
    #this does not work. it looks correct but it is not working correctly
    references_counter = Counter({"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    entities_counter = Counter({"tp": 0, "fp": 0, "fn": 0, "tn": 0})

    #clean up data the same way we do in "linking.ipynb"
    
    gt_data = []
    linked_data = []

    input_linked = linked
    gt = gt

    gt = clean_gt(gt)
    gt_data += gt
    #here, unlike in "linking.ipynb" I also add the gnd_ids since that is the only way we have the candidates
    input_linked = clean_raw(input_linked)
    #print("depois")
    #print(input_linked[1])

    #due to non-determinism in the flair NER:
    all_refs_gt = [g["page"]+g["coord"] for g in gt] 
    all_refs_linked = [ent["page"]+ent["coord"] for l in input_linked for ent in l]
    all_valid_refs = set(all_refs_gt).intersection(set(all_refs_linked))

    for ent_variations in input_linked:
        ent_instances = []
        for ent in ent_variations:
            if (ent["page"]+ent["coord"]) in all_valid_refs:
                ent_instances.append({"ent": ent, "label": label_entity(ent, gt)})
        if ent_instances:
            linked_data.append(ent_instances)
    
    #but now linked_data is on reference level, we want to aggregate them:
    ent_cand_label = []
    from tqdm import tqdm
    for entity_list in tqdm(linked_data, smoothing=0.01):
        coord_list = []
        label_list = []
        candidates_list = []
        #now i need the candidates, in the rulebased case we only have access to the gnd_ids
        for ent_dict in entity_list:
            ent = ent_dict["ent"]
            coord_list.append({
                "page": ent.pop("page", ""), 
                "coords": ent.pop("coord", "")
            })
            label_list.append(ent_dict["label"])
            candidates_list.append(ent["gnd_candidates"])
        ent_cand_label.append({"entity": ent, "candidates": candidates_list, "occurences": coord_list, "labels": label_list})

    #reference-level, so aggregate by reference:
    #references_counter = eval_references(gt, linked, references_counter)
    #entity-level, so aggregate by entity:
    #entities_counter = eval_entities(gt, linked, entities_counter)

    list_of_good_entities = []
    list_of_problematic_entities = []
    for ent_dict in tqdm(ent_cand_label):
        if len(set(ent_dict["labels"])) > 1:
            for label in set(ent_dict["labels"]):
                ent_dict["label"] = label
                #features = candidates_to_features(ent=ent_dict["entity"], candidates=ent_dict["candidates"], gt_label=ent_dict["label"])
                #ent_dict.update(features)
                list_of_problematic_entities.append(ent_dict.copy())
        else:
            ent_dict["label"] = set(ent_dict["labels"]).pop()
            #features = candidates_to_features(ent=ent_dict["entity"], candidates=ent_dict["candidates"], gt_label=ent_dict["label"])
            #ent_dict.update(features)
            list_of_good_entities.append(ent_dict)
        

    list_of_all_entities = (list_of_good_entities + list_of_problematic_entities)
    scores_entity = Scores()
    scores_mention = Scores()
    for entity in list_of_all_entities:
        scores_entity.update_counter(counts_dict=eval_entity(entity))
        # we have around 200 references too many. 
        scores_mention.update_counter(counts_dict=eval_mentions(entity))

    #print("F1 Ent:", scores_entity.get_score()["F1"], "F1 Ment:", scores_mention.get_score()["F1"])
    #return ent_scores, ment_scores
    references_counter["tp"] = scores_mention.get_score()["tp"]
    references_counter["fp"] = scores_mention.get_score()["fp"]
    references_counter["tn"] = scores_mention.get_score()["tn"]
    references_counter["fn"] = scores_mention.get_score()["fn"]

    entities_counter["tp"] = scores_entity.get_score()["tp"]
    entities_counter["fp"] = scores_entity.get_score()["fp"]
    entities_counter["tn"] = scores_entity.get_score()["tn"]
    entities_counter["fn"] = scores_entity.get_score()["fn"]
    return entities_counter 