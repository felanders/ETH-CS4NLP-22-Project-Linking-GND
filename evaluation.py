from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
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

def filter_ids(ids, scores, top_n=10, treshold=0.5):
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
            if score > treshold:
                filtered.append(id)
            else:
                break
    if len(filtered) >= 1:
        return filtered 
    else:
        return [""]

def eval_entity(entity, top_n=10, treshold=0.5):
    filtered_ids = filter_ids(entity["ids"], scores=entity["scores"], top_n=top_n, treshold=treshold)
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    if entity["label"] in filtered_ids:
        key = label_and_match_to_key(gt_label=entity["label"], match=True)
    else:
        key = label_and_match_to_key(gt_label=entity["label"], match=False)
    counts[key] += 1
    return counts

def eval_mentions(entity, top_n=10, treshold=0.5):
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0} 
    filtered_ids = filter_ids(entity["ids"], scores=entity["scores"], top_n=top_n, treshold=treshold)
    for label in entity["labels"]:
        if label in filtered_ids:
            key = label_and_match_to_key(gt_label=entity["label"], match=True)
        else:
            key = label_and_match_to_key(gt_label=entity["label"], match=False)
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

def perform_experiment(keep_empty, do_sample, oversampling, balance, d, model, n_s, tresholds, verbose=False):
    X_train, y_train = get_x_y(d["train"], keep_empty_candidate=keep_empty)

    if do_sample:
        df = pd.DataFrame(X_train)
        df["y"] = y_train
        
        count = df["y"].count()
        pos_samples = df["y"].sum()

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
        X_sample = sample[[0, 1, 2, 3, 4, 5, 6, 7]]
    else:
        y_sample = y_train
        X_sample = X_train

    model.fit(X_sample, y_sample)

    for entity in d["eval"]:
        ranking = rank_candidates(candidates=entity["candidates"], features=entity["features"], model=model)
        entity.update(ranking)

    ent_scores = []
    ment_scores = []

    for top_n in n_s:
        print("Top: ", top_n) if verbose else ""
        for treshold in tresholds:
            scores_entity = Scores()
            scores_mention = Scores()
            for entity in d["eval"]:
                scores_entity.update_counter(counts_dict=eval_entity(entity, top_n=top_n, treshold=treshold))
                scores_mention.update_counter(counts_dict=eval_mentions(entity, top_n=top_n, treshold=treshold))

            ent_scores.append({"top_n": top_n, "treshold": treshold, "score": scores_entity})
            ment_scores.append({"top_n": top_n, "treshold": treshold, "score": scores_mention})
            print("Treshold: ", treshold, "F1 Ent:", scores_entity.get_score()["F1"], "F1 Ment:", scores_mention.get_score()["F1"]) if verbose else ""
    return ent_scores, ment_scores

def plot_metrics_over_treshold(tresholds, n_s, oversampling, balance, do_sample, keep_empty, model, data, results):

    y = np.zeros((6, len(n_s), len(tresholds)))

    def get_scores(di, top_n=10, treshold=0.5):
        for scores_dict in di["ent_scores"]:
            if scores_dict["top_n"] == top_n and scores_dict["treshold"] == treshold:
                ent_scores = scores_dict["score"].get_score()

        for scores_dict in di["ment_scores"]:
            if scores_dict["top_n"] == top_n and scores_dict["treshold"] == treshold:
                ment_scores = scores_dict["score"].get_score()
        return ent_scores, ment_scores

    for di in results:
        # Keep only stuff that matches, do_sample, keep_empty, oversamplint, balance, model, and data
        if di["do_sample"] == do_sample and di["keep_empty"] == keep_empty and di["oversampling"] == oversampling and di["balance"] == balance and di["model"] == model and di["data"] == data:
            for n_i, n in enumerate(n_s):
                for t_i, t in enumerate(tresholds):
                    ent_scores, ment_scores = get_scores(di, top_n=n, treshold=t)
                    for i, score in enumerate(["F1", "Recall", "Precision"]):
                        y[i, n_i, t_i ] = ent_scores[score]
                        y[i+3, n_i, t_i] = ment_scores[score]

    fig, axs = plt.subplots(2, 3, figsize=(30, 20))  
    fig.suptitle(f"Oversampling: {oversampling}, Balance: {balance}")
    col = ["g", "y", "r", "b"]

    for ax, scores, score_type in zip(axs.flat, y, ["Entity F1", "Entity Recall", "Entity Precision"] +["Mention F1", "Mention Recall", "Mention Precision"]):
        for i, score in enumerate(n_s):
            ax.plot(tresholds, scores[i], f"{col[i]}", label=f"N: {score}")
            ax.set_title(f"{score_type}")
            #ax.set_ylim(0,1.1)
            ax.legend()
    fig.savefig(fname=f"plots/Over_{oversampling}_Bal_{balance}")