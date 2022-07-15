from collections import Counter
from typing import final
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
from utils import get_gnd

class Scores:
    def __init__(self, counts_dict={"tp": 0, "fp": 0, "fn": 0, "tn": 0}):
        self.counter = Counter(counts_dict)
        self.precision = 0
        self.recall = 0
        self.f1 = 0
        self.accuracy = 0

    def compute_scores(self):
        self.precision = self.counter["tp"]/(self.counter["tp"] + self.counter["fp"]) if self.counter["tp"] + self.counter["fp"] != 0 else 0
        self.recall = self.counter["tp"]/(self.counter["tp"] + self.counter["fn"]) if self.counter["tp"] + self.counter["fn"] != 0 else 0
        self.f1 = 2 * self.counter["tp"]/(2*self.counter["tp"] + self.counter["fp"] + self.counter["fn"]) if self.counter["tp"] + self.counter["fp"] + self.counter["fn"] != 0 else 0
        self.accuracy = (self.counter["tp"]+self.counter["tn"])/(self.counter["tp"]+self.counter["tn"]+self.counter["fp"]+self.counter["fn"])

    def update_counter(self, counts_dict):
        self.counter.update(counts_dict)
    
    def divide_scores_for_crossval(self, divide_by):
        for key in ["tp", "fp", "tn", "fn"]:
            self.counter[key] = int(self.counter[key]/divide_by)

    def get_counter(self):
        return self.counter

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

    def print_scores(self):
        result = self.get_score()
        print("F1:", result["F1"], "RE: ", result["Recall"], "PR:", result["Precision"], "AC:", result["Accuracy"])
        print("TP:", result["tp"], "FN:", result["fn"], "FP", result["fp"], "TN", result["tn"])
        print("\n")

def rank_candidates(candidates, features, model):
    candidate_scores = []
    candidate_ids = []
    
    for candidate, feature in zip(candidates, features):
        score = model.predict(np.array(feature).reshape(1,-1))[0]
        candidate_scores.append(score)
        candidate_ids.append(get_gnd(candidate))
    
    if candidate_ids:
        candidate_ids = np.array(candidate_ids)
        indices = np.argsort(candidate_scores)
        ids_sorted = np.array(candidate_ids)[indices[::-1]]
        scores_sorted = np.array(candidate_scores)[indices[::-1]]
        return {"ids": ids_sorted, "scores": scores_sorted}
    else:
        return {"ids": [], "scores": []}

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

def filter_ids(ids, scores, top_n=10, threshold=0.5):
    """ids and scores are expected to be ordered"""
    filtered = []
    n = 0
    for id, score in zip(ids, scores):
        if n > top_n:
            if n >= 1:
                return filtered
            else:
                return [""]
        else:
            n += 1
            if score > threshold:
                filtered.append(id)
            else:
                break
    if len(filtered) >= 1:
        return filtered 
    else:
        return [""]

def eval_entity(entity, top_n=10, threshold=0.5):
    filtered_ids = filter_ids(entity["ids"], scores=entity["scores"], top_n=top_n, threshold=threshold)
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    
    if entity["label"] in filtered_ids:
        key = label_and_match_to_key(gt_label=entity["label"], match=True)
    else:
        key = label_and_match_to_key(gt_label=entity["label"], match=False)
    counts[key] += 1
    
    return counts

def eval_mentions(entity, top_n=10, threshold=0.5):
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0} 
    filtered_ids = filter_ids(entity["ids"], scores=entity["scores"], top_n=top_n, threshold=threshold)

    #This is because GR calls "labels" "gt_label"
    key_helper = "labels"
    if key_helper not in entity:
        key_helper = "gt_label"

    for label in entity[key_helper]:
        if label in filtered_ids:
            key = label_and_match_to_key(gt_label=label, match=True)
        else:
            key = label_and_match_to_key(gt_label=label, match=False)
        counts[key] += 1

    return counts

def y_to_number(y):
    if y == "tp" or y == "tn":
        return 1
    elif y == "fp" or y == "fn":
        return 0

def get_x_y(list_of_entities, keep_empty_candidate=False):
    X = []
    y = []
    for ent_dict in list_of_entities:
        for y_ent, features, cand in zip(ent_dict["y"], ent_dict["features"], ent_dict["candidates"]):
            if not keep_empty_candidate and get_gnd(cand) == "":
                pass
            else:
                y.append(y_to_number(y_ent))
                X.append(features)
    return X, y

def perform_experiment(keep_empty, do_sample, oversampling, balance, train, eval, model, n_s, thresholds, verbose=False):
    X_train, y_train = get_x_y(train, keep_empty_candidate=keep_empty)
    feature_length = len(X_train[0])
    # import pdb; pdb.set_trace()

    if do_sample:
        df = pd.DataFrame(X_train)
        df["y"] = y_train
        
        count = df["y"].count()
        pos_samples = df["y"].sum()

        #TODO check if this sampling is correct
        def sampling_strategy(x, over_sampling, balance):
            if x.shape[0] > pos_samples:
                if pos_samples*over_sampling*balance < count:
                    return x.sample(pos_samples*over_sampling*balance)
                else:
                    return x.sample(count)
            else:
                return x.sample(pos_samples*over_sampling, replace=True)

        sample = df.groupby('y', group_keys=False).apply(lambda x: sampling_strategy(x, over_sampling=oversampling, balance=balance))

        y_sample = sample["y"]
        X_sample = sample[range(feature_length)]
    else:
        y_sample = y_train
        X_sample = X_train
    
    # X_sample = X_sample.fillna(0)
    # print(X_sample[X_sample.isna().any(axis=1)])
    # adsadasddas

    model.fit(X_sample, y_sample)

    for entity in eval:
    #for entity in d["test"]:
        # print('len features:', len(entity['features'][0]), 'len candidates:', len(entity['candidates'][0]))
        ranking = rank_candidates(candidates=entity["candidates"], features=entity["features"], model=model)
        entity.update(ranking)

    ent_scores = []
    ment_scores = []

    for top_n in n_s:
        print("Top: ", top_n) if verbose else ""
        for threshold in thresholds:
            scores_entity = Scores()
            scores_mention = Scores()
            for entity in eval:
            #for entity in d["test"]:
                scores_entity.update_counter(counts_dict=eval_entity(entity, top_n=top_n, threshold=threshold))
                scores_mention.update_counter(counts_dict=eval_mentions(entity, top_n=top_n, threshold=threshold))

            ent_scores.append({"top_n": top_n, "threshold": threshold, "score": scores_entity})
            ment_scores.append({"top_n": top_n, "threshold": threshold, "score": scores_mention})
            print("threshold: ", threshold, "F1 Ent:", scores_entity.get_score()["F1"], "F1 Ment:", scores_mention.get_score()["F1"]) if verbose else ""
    return ent_scores, ment_scores

def crossvalidate_experiment(train, eval, n_fold, keep_empty, do_sample, oversampling, balance, model, n_s, thresholds, verbose=False):
    data = train + eval
    chunk = math.floor(len(data)/n_fold)
    ent_scores_crossval = []
    ment_scores_crossval = []
    for i in range(n_fold):
        lb = i*chunk
        ub = (i+1)*chunk
        train = data[:lb]+ data[ub:]
        eval = data[lb:ub]
        ent_scores, ment_scores = perform_experiment(
            keep_empty=keep_empty, 
            do_sample=do_sample, 
            oversampling=oversampling, 
            balance=balance, 
            model=model, 
            n_s=n_s, 
            thresholds=thresholds, 
            train=train, 
            eval=eval, 
            verbose=verbose)
        ent_scores_crossval.append(ent_scores)
        ment_scores_crossval.append(ment_scores)

    mean_ent_scores = ent_scores_crossval[0]
    mean_ment_scores = ment_scores_crossval[0]
    for ent_scores, ment_scores in zip(ent_scores_crossval[1:], ment_scores_crossval[1:]):
        for mean_ent_score, ent_score in zip(mean_ent_scores, ent_scores):
            mean_ent_score["score"].update_counter(ent_score["score"].get_counter())
        for mean_ment_score, ment_score in zip(mean_ment_scores, ment_scores):
            mean_ment_score["score"].update_counter(ment_score["score"].get_counter())
    for ent_score, ment_score in zip(mean_ent_scores, mean_ment_scores):
        ent_score["score"].divide_scores_for_crossval(divide_by=n_fold)
        ment_score["score"].divide_scores_for_crossval(divide_by=n_fold)
    return mean_ent_scores, mean_ment_scores

def plot_metrics_over_threshold(thresholds, n_s, oversampling, balance, do_sample, keep_empty, model, data, results):

    y = np.zeros((6, len(n_s), len(thresholds)))

    def get_scores(di, top_n=10, threshold=0.5):
        for scores_dict in di["ent_scores"]:
            if scores_dict["top_n"] == top_n and scores_dict["threshold"] == threshold:
                ent_scores = scores_dict["score"].get_score()

        for scores_dict in di["ment_scores"]:
            if scores_dict["top_n"] == top_n and scores_dict["threshold"] == threshold:
                ment_scores = scores_dict["score"].get_score()
        return ent_scores, ment_scores

    for di in results:
        # Keep only stuff that matches, do_sample, keep_empty, oversamplint, balance, model, and data
        if di["do_sample"] == do_sample and di["keep_empty"] == keep_empty and di["oversampling"] == oversampling and di["balance"] == balance and di["model"] == model and di["data"] == data:
            for n_i, n in enumerate(n_s):
                for t_i, t in enumerate(thresholds):
                    ent_scores, ment_scores = get_scores(di, top_n=n, threshold=t)
                    for i, score in enumerate(["F1", "Recall", "Precision"]):
                        y[i, n_i, t_i ] = ent_scores[score]
                        y[i+3, n_i, t_i] = ment_scores[score]

    fig, axs = plt.subplots(2, 3, figsize=(30, 20))  
    fig.suptitle(f"Oversampling: {oversampling}, Balance: {balance}")
    col = ["g", "y", "r", "b"]

    for ax, scores, score_type in zip(axs.flat, y, ["Entity F1", "Entity Recall", "Entity Precision"] +["Mention F1", "Mention Recall", "Mention Precision"]):
        for i, score in enumerate(n_s):
            ax.plot(thresholds, scores[i], f"{col[i]}", label=f"N: {score}")
            ax.set_title(f"{score_type}")
            #ax.set_ylim(0,1.1)
            ax.legend()
    fig.savefig(fname=f"plots/Over_{oversampling}_Bal_{balance}")