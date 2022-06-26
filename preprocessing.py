def clean_gt(gt):
    result = []
    for ent in gt:
        if "type" in ent and ent["type"] == "PER":
            references = ent["references"]
            del ent["references"]
            for ref_list in references:
                for ref in ref_list:
                    ent.update(ref)
                    result.append(ent)
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
                dictionary["firstname"] = ent["firstname"][0]
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
            if "references" in ent:
                for page, refs in ent["references"].items():
                    dictionary.update({
                        "page": page,
                        "year": page.split("_")[1]
                    })
                    for ref in refs:
                        if "coords" in ref:
                            for coord in ref["coords"]:
                                dictionary.update({"coord": coord.split(":")[0]})
                                ent_mentions.append(dictionary)
            result.append(ent_mentions)
    return result

def label_entity(ent, gt):
    page = ent["page"]
    coord = ent["coord"]
    for g in gt:
        if g["page"] == page:
            if g["coord"] == coord:
                return g["Gnd"]
    return ""