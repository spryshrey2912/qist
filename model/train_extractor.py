"""Fine-tune xlm-roberta-base to find the 7 terms. Run in Google Colab (GPU on):
  !pip install transformers datasets seqeval accelerate
  !python model/train_extractor.py
Reads data/train.csv + data/test_real.csv (made by data/split.py), prints precision/recall per term."""
import json, random
import pandas as pd, numpy as np, torch
from transformers import (AutoTokenizer, AutoModelForTokenClassification, Trainer,
                          TrainingArguments, DataCollatorForTokenClassification)
from seqeval.metrics import classification_report

TERMS = ["cash_price","n_installments","installment_amount","admin_fee","late_fee","profit_rate","shariah_claim"]
LABELS = ["O"] + [f"{p}-{t}" for t in TERMS for p in ("B", "I")]
L2I = {l: i for i, l in enumerate(LABELS)}
MODEL = "xlm-roberta-base"
tok = AutoTokenizer.from_pretrained(MODEL)

train_df = pd.read_csv("data/train.csv")           # run data/split.py first
test_df = pd.read_csv("data/test_real.csv")        # REAL offers only, from providers the model never saw in training
test_synth_df = pd.read_csv("data/test_synth.csv") # synthetic sanity check (easy; do not quote as the headline score)
# real offers are rare and harder than the synthetic ones, so show the model each real row 6 times
train_df = pd.concat([train_df] + [train_df[train_df.source == "real"]] * 5).sample(frac=1, random_state=1).reset_index(drop=True)
print("train", len(train_df), "test_real", len(test_df), "test_synth", len(test_synth_df))

def encode(row):
    enc = tok(row["text"], return_offsets_mapping=True, truncation=True, max_length=512)
    spans = json.loads(row["spans"])
    labels = []
    for (s, e), in_special in zip(enc["offset_mapping"], enc.get("special_tokens_mask", [0]*len(enc["input_ids"]))):
        if s == e: labels.append(-100); continue          # special token
        lab = "O"
        for ss, se, t in spans:
            if s < se and e > ss:                         # token overlaps this span
                lab = ("B-" if s <= ss else "I-") + t
                break
        labels.append(L2I[lab])
    enc["labels"] = labels
    enc.pop("offset_mapping")
    return enc

class DS(torch.utils.data.Dataset):
    def __init__(self, d): self.items = [encode(r) for _, r in d.iterrows()]
    def __len__(self): return len(self.items)
    def __getitem__(self, i): return self.items[i]

model = AutoModelForTokenClassification.from_pretrained(
    MODEL, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=L2I)
args = TrainingArguments("model/out", num_train_epochs=25, per_device_train_batch_size=8,
                         learning_rate=5e-5, warmup_steps=20, weight_decay=0.01, save_strategy="no", report_to=[])
trainer = Trainer(model=model, args=args, train_dataset=DS(train_df), eval_dataset=DS(test_df),
                  data_collator=DataCollatorForTokenClassification(tok))
trainer.train()

def report(df, name):
    pred = trainer.predict(DS(df))
    p = np.argmax(pred.predictions, axis=2)
    y_true, y_pred = [], []
    for pr, lb in zip(p, pred.label_ids):
        y_true.append([LABELS[l] for l in lb if l != -100])
        y_pred.append([LABELS[x] for x, l in zip(pr, lb) if l != -100])
    print("\n=====", name, "=====")
    print(classification_report(y_true, y_pred, zero_division=0))   # precision / recall per term

report(train_df, "TRAIN (sanity check: should be high; if not, the pipeline is broken)")
report(test_synth_df, "TEST synthetic (easy)")
report(test_df, "TEST REAL (the score that counts)")

# ---- real-test scoring on whole spans (the way the app will use the model) ----
from seqeval.metrics.sequence_labeling import get_entities
TRIM = " \t\n.,;:()[]|،؛"

def repair(text, spans):
    """Subword pieces split values like 'Shari|ah' or '3 Mont|s'. Grow each span to whole words,
    trim punctuation, and merge neighbours of the same type. (The labelled data is not changed.)"""
    out = []
    for t, a, b in spans:
        while a > 0 and not text[a-1].isspace(): a -= 1
        while b < len(text) and not text[b].isspace(): b += 1
        while a < b and text[a] in TRIM: a += 1
        while b > a and text[b-1] in TRIM: b -= 1
        if a < b: out.append([t, a, b])
    out.sort(key=lambda x: (x[1], x[2]))
    merged = []
    for t, a, b in out:
        if merged and merged[-1][0] == t and text[merged[-1][2]:a].strip() == "":
            merged[-1][2] = max(merged[-1][2], b)
        elif merged and merged[-1][0] == t and a < merged[-1][2]:
            merged[-1][2] = max(merged[-1][2], b)
        else:
            merged.append([t, a, b])
    return [tuple(x) for x in merged]

pred = trainer.predict(DS(test_df)); P = np.argmax(pred.predictions, axis=2)
stats = {m: {t: [0, 0, 0] for t in TERMS} for m in ("exact", "overlap")}   # tp, n_pred, n_gold
print("\n===== WRONG CASES (real test, after span repair) =====")
for (_, row), pr, lb in zip(test_df.iterrows(), P, pred.label_ids):
    text = row["text"]
    enc = tok(text, return_offsets_mapping=True, truncation=True, max_length=512)
    offs = [o for o in enc["offset_mapping"] if o[0] != o[1]]
    tags = [LABELS[x] for x, l in zip(pr, lb) if l != -100]
    got = repair(text, [(t, offs[a][0], offs[b][1]) for t, a, b in get_entities(tags)])
    gold = [(t, a, b) for a, b, t in json.loads(row["spans"])]
    for mode in ("exact", "overlap"):
        used = set()
        for t in TERMS:
            G = [g for g in gold if g[0] == t]; Pp = [g for g in got if g[0] == t]
            tp = 0
            for pg in Pp:
                for k, g in enumerate(G):
                    if (t, k) in used: continue
                    ok = (pg[1:] == g[1:]) if mode == "exact" else (pg[1] < g[2] and g[1] < pg[2])
                    if ok: used.add((t, k)); tp += 1; break
            stats[mode][t][0] += tp; stats[mode][t][1] += len(Pp); stats[mode][t][2] += len(G)
    for t, a, b in sorted(set(gold) - set(got)): print(f"{row['id']} MISSED  {t}: {text[a:b]!r}")
    for t, a, b in sorted(set(got) - set(gold)): print(f"{row['id']} WRONG   {t}: {text[a:b]!r}")
for mode in ("exact", "overlap"):
    print(f"\n===== REAL TEST, {mode.upper()} span match =====")
    TP = NP = NG = 0
    for t in TERMS:
        tp, npred, ngold = stats[mode][t]; TP += tp; NP += npred; NG += ngold
        pr_ = tp / npred if npred else 0; rc = tp / ngold if ngold else 0
        print(f"{t:20s} precision {pr_:.2f}  recall {rc:.2f}  f1 {(2*pr_*rc/(pr_+rc) if pr_+rc else 0):.2f}  (gold {ngold})")
    pr_ = TP / NP if NP else 0; rc = TP / NG if NG else 0
    print(f"{'ALL':20s} precision {pr_:.2f}  recall {rc:.2f}  f1 {(2*pr_*rc/(pr_+rc) if pr_+rc else 0):.2f}")

trainer.save_model("model"); tok.save_pretrained("model")
print("Saved to model/  (download this folder from Colab)")
