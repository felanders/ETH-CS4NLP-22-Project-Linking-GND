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

problematic_ref = ["dkm-003_1990_050_0396.txt349,2205,129,24"]
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
    def __init__(self, counts_dict={"TP": 0, "FP": 0, "FN": 0}):
        self.counter = Counter(counts_dict)
        self.precision = 0
        self.recall = 0
        self.f1 = 0

    def compute_scores(self):
        self.precision = self.counter["TP"]/(self.counter["TP"] + self.counter["FP"]) if self.counter["TP"] + self.counter["FP"] != 0 else 0
        self.recall = self.counter["TP"]/(self.counter["TP"] + self.counter["FN"]) if self.counter["TP"] + self.counter["FN"] != 0 else 0
        self.f1 = 2 * self.counter["TP"]/(2*self.counter["TP"] + self.counter["FP"] + self.counter["FN"]) if self.counter["TP"] + self.counter["FP"] + self.counter["FN"] != 0 else 0
    
    def update_counter(self, counts_dict):
        self.counter.update(counts_dict)

    def get_score(self, round_to=3):
        self.compute_scores()
        result = {
            "TP": self.counter["TP"],
            "FP": self.counter["FP"],
            "FN": self.counter["FN"],
            "Precision": round(self.precision,round_to),
            "Recall": round(self.recall, round_to),
            "F1": round(self.f1, round_to)
        }
        return result

def true_positive(ref, gt_ref_list):
    for gt_ref in gt_ref_list:
        if ref['page'] == gt_ref["page"] and ref['coord'] == gt_ref["coord"]:
            return True
    return False

def false_negative(ref, linked_refs):
    for linked_ref in linked_refs:
        if ref['page'] == linked_ref["page"] and ref['coord'] == linked_ref["coord"]:
            return False
    return True

def compare_references(linked_refs, gt_ref_list, pages):
    tp = 0
    fp = 0
    fn = 0
    sanity = []
    for ref in linked_refs:
        if true_positive(ref=ref, gt_ref_list=gt_ref_list):
            sanity.append(ref["uniqueid"])
            tp += 1
        else:
            fp += 1
    # for ref in gt_ref_list:
    #     if false_negative(ref=ref, linked_refs=linked_refs):
    #         fn += 1
    return [Counter({"TP": tp, "FP": fp, "FN": fn}),sanity]

def flatten_linked_dict(linked_dict, convenience = False):
    linked_gnd_dict = {}
    if convenience:
        for ent in linked_dict:
            if 'type' in ent and ent['type'] == 'PER':
                ref_list = []
                for key in ent["references"]:
                    if key in context_pages: continue

                    normalized_coords = set()
                    for coords in ent["references"][key][0]["coords"]:
                        #clean them up first
                        coords_clean = str(coords).split(":")[0]
                        coords_clean = str(coords_clean).split(";")
                        for i in coords_clean:
                            normalized_coords.add(i) 
                        #this is because sometimes the same coord could be present but with different suffixes so
                        # "1294,473,237,23:main","1294,473,237,23:rpunc" for example

                    for coords in normalized_coords:    
                        ref_list.append({"page": key, "coord": coords, "uniqueid":  key+coords})
        return ref_list
    else:
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
    #deal with inconsistent gt data
    all_refs_gt = get_all_refs_gt(gt)
    all_refs_linked = get_all_refs_linked(linked)
    all_valid_refs = set(all_refs_gt).intersection(all_refs_linked)
    
    #aggregate by reference, only for entries with a gndid:
    ref_dict_gt = (agg_by_ref_gt(gt))
    ref_dict_linked = (agg_by_ref_linked(linked))

    print(len(all_valid_refs.intersection(ref_dict_gt)))
    all_positives = all_valid_refs.intersection(ref_dict_gt)

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

                references_counter["TP"] += 1

                assert(visited_pos[uniqueid] == False)
                visited_pos[uniqueid] = True
            else:
                assert(visited_linked[uniqueid] == False)
                visited_linked[uniqueid] = True

                references_counter["FN"] += 1

                assert(visited_pos[uniqueid] == False)
                visited_pos[uniqueid] = True
        if uniqueid not in ref_dict_linked:

            references_counter["FN"] += 1

            assert(visited_pos[uniqueid] == False)
            visited_pos[uniqueid] = True

    for uniqueid in ref_dict_linked:
        if uniqueid not in all_valid_refs:
            continue
        if visited_linked[uniqueid] == False:
            references_counter["FP"] += 1
            
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
                        if ent["gnd_ids"] != []:
                            if ent_id in ent_to_uniqueids_dict:
                                ent_to_uniqueids_dict[ent_id]["uniqueids"].append(page+coords)
                            else: 
                                ent_to_uniqueids_dict.setdefault(ent_id,value)
            ent_id += 1
    return ent_to_uniqueids_dict

def eval_entities(gt,linked_dict, entities_counter):
    #TODO rewrite to handle that entities are not the same in gt and linked
    ent_dict_gt = agg_by_ent_gt(gt)
    ent_dict_linked = create_ent_to_uniqueids_dict(linked_dict)
    visited_linked = dict()
    visited_gt = dict()
    for i in ent_dict_linked.keys():
        visited_linked.setdefault(i, False)
    for i in ent_dict_gt.keys():
        visited_gt.setdefault(i, False)

    for gnd_id_gt in ent_dict_gt:
        unique_ids_gt = [x["uniqueid"] for x in ent_dict_gt[gnd_id_gt]]
        for ent in ent_dict_linked:
            if visited_linked[ent]:
                continue
            
            if ent_dict_linked[ent]["uniqueids"] == unique_ids_gt:
                if gnd_id_gt in ent_dict_linked[ent]["gnds"]:
                    entities_counter["TP"] += 1
                elif ent_dict_linked[ent]["gnds"] == []:
                    entities_counter["FN"] += 1
                else:
                    entities_counter["FP"] += 1
                visited_linked[ent] = True
                visited_gt[gnd_id_gt] = True
            else:
                if ent_dict_linked[ent]["uniqueids"] != [] and (set(ent_dict_linked[ent]["uniqueids"]).issubset(set(unique_ids_gt))):
                    if gnd_id_gt in ent_dict_linked[ent]["gnds"]:
                        entities_counter["TP"] += 1
                    elif ent_dict_linked[ent]["gnds"] == []:
                        entities_counter["FN"] += 1
                    else:
                        entities_counter["FN"] += 1 #But i am not sure about this NOTE
                    visited_linked[ent] = True
                    visited_gt[gnd_id_gt] = True
    #and now i still need to count the rest of the FP :
    for i in visited_linked:
        if not visited_linked[i]:
            if ent_dict_linked[i]["gnds"] != []:
                entities_counter["FP"] += 1
    #and the rest of the FN because i don't think the line above counts them correctly:
    for i in visited_gt:
        if not visited_gt[i]:
            entities_counter["FN"] += 1
    return entities_counter

def evaluate_person(gt,linked,pages):
    #this does not work. it looks correct but it is not working correctly
    references_counter = Counter({"TP": 0, "FP": 0, "FN": 0})
    entities_counter = Counter({"TP": 0, "FP": 0, "FN": 0})
    #reference-level, so aggregate by reference:
    references_counter = eval_references(gt, linked, references_counter)
    #entity-level, so aggregate by entity:
    entities_counter = eval_entities(gt, linked, entities_counter)

    return references_counter 

def evaluate_person_AFGR(gt, linked, pages):
    pages = [x for x in pages if x not in context_pages]
    references_counter = Counter({"TP": 0, "FP": 0, "FN": 0})
    entities_counter = Counter({"TP": 0, "FP": 0, "FN": 0})
    # restructure the list of ground truth references for easier indexing



    gt_gnd_dict = flatten_gt_dict(gt_dict=gt, pages=pages)
    linked_gnd_dict = flatten_linked_dict(linked_dict=linked)

    #might be worth it to just change "flatten_xx_dict"
    inv_linked_gnd_dict = dict()
    for k,v in linked_gnd_dict.items():
        for refs in v:
            inv_linked_gnd_dict.setdefault(refs["uniqueid"],[]).append(k)
    
    inv_gt_gnd_dict = dict()
    for k,v in gt_gnd_dict.items():
        for refs in v:
            inv_gt_gnd_dict.setdefault(refs["uniqueid"],[]).append(k)

    linked_gnd_dict_cleaned = linked_gnd_dict.copy()
    #print("len(linked_gnd_dict_cleaned)")
    #print(len(linked_gnd_dict_cleaned))
    sanity_check_entities = dict()
    sanity_check_references = dict()
    sanity_check_uniqueid = []
    for gnd_id in gt_gnd_dict:
        sanity_check_entities.setdefault(gnd_id, False)
        for ref in gt_gnd_dict[gnd_id]:
            sanity_check_uniqueid.append(ref["uniqueid"])
            sanity_check_references.setdefault(ref["uniqueid"], False)


    for gnd_id in linked_gnd_dict:
        if gnd_id not in linked_gnd_dict_cleaned.keys(): continue #we excluded the entity linked to this gndid earlier with another gndid
        if gnd_id in gt_gnd_dict:
            linked_refs = linked_gnd_dict[gnd_id]
            [counts, sanity] = compare_references(linked_refs, gt_ref_list = gt_gnd_dict[gnd_id], pages=pages)
            references_counter.update(counts)

            for i in sanity:
                assert(sanity_check_references[i] == False)
                sanity_check_references[i] = True

            entities_counter["TP"] += 1
            assert(sanity_check_entities[gnd_id] == False)
            sanity_check_entities[gnd_id] = True

            # we do not want to count this entity again:
            for refs in linked_refs:
                for gnd_id_candidate in inv_linked_gnd_dict[refs["uniqueid"]]:
                    if gnd_id_candidate in linked_gnd_dict_cleaned.keys():
                        linked_gnd_dict_cleaned.pop(gnd_id_candidate)
    

    #invert linked_gnd_dict_cleaned
    inv_linked_gnd_dict_cleaned = dict()
    for gnd_id in linked_gnd_dict_cleaned:
        linked_refs = linked_gnd_dict_cleaned[gnd_id]
        for ref in linked_refs:
            inv_linked_gnd_dict_cleaned[ref["uniqueid"]] = inv_linked_gnd_dict[ref["uniqueid"]]
    
    references_fp = set()
    for gnd_id in linked_gnd_dict_cleaned:
        if gnd_id not in gt_gnd_dict:
            # The GND ID is not in the gt thus all found references are false positives
            linked_refs = linked_gnd_dict[gnd_id]
            for i in [ref["uniqueid"] for ref in linked_refs]:
                references_fp.add(i)
    references_counter["FP"] += (len(references_fp))

    #TODO adjust evaluation for references as well, this currently does not work correctly.
    #TODO: i made this so ugly when it was so clean and nice before, refactor it.

    #print("len(inv_linked_gnd_dict_cleaned)")
    #print(len(inv_linked_gnd_dict_cleaned))
    entities_counter["FP"] = len(inv_linked_gnd_dict_cleaned)
    
    # count false negatives
    for gnd_id in gt_gnd_dict:
        for ref in gt_gnd_dict[gnd_id]:
            if sanity_check_references[ref["uniqueid"]] == False:
                # count all references in the gt that are on the same page but not in the
                #references_counter.update({"FN": len([ref for ref in gt_gnd_dict[gnd_id] if ref["page"] in pages])})
                references_counter["FN"] += 1
        
        if gnd_id not in linked_gnd_dict: #NOTE this is a very generous choice... might change it later 
            entities_counter["FN"] += 1 
    return references_counter

