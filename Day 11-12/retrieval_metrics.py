"""Hit@5 and MRR without a judge (Day 12, Exercise 3 step 4).

Compares the labelled source_document in test_questions.json with the sources in context_sources
of a pipeline_outputs file. Questions labelled "multiple" or null (unanswerable) are skipped.
No API calls, same result every run. Writes retrieval_metrics_<label>.json.

    uv run python retrieval_metrics.py                                  # pipeline_outputs_local.json
    uv run python retrieval_metrics.py pipeline_outputs.json
"""

import json
import sys

outputs_file = sys.argv[1] if len(sys.argv) > 1 else "pipeline_outputs_local.json"

with open("test_questions.json", encoding="utf-8") as f:
    labels = {q["id"]: q.get("source_document") for q in json.load(f)}
with open(outputs_file, encoding="utf-8") as f:
    rows = json.load(f)

per_question = []
print(f"{'id':<5} {'labelled source':<30} rank")
for r in rows:
    label = labels.get(r["id"])
    if label in (None, "", "multiple") or isinstance(label, list):
        continue
    sources = [c["source"] for c in r["context_sources"]][:5]
    rank = sources.index(label) + 1 if label in sources else None
    per_question.append({"id": r["id"], "source_document": label, "rank": rank})
    print(f"{r['id']:<5} {label:<30} {rank or 'not in top 5'}")

ranks = [p["rank"] for p in per_question]
hit5 = sum(rk is not None for rk in ranks) / len(ranks)
mrr = sum(1 / rk for rk in ranks if rk) / len(ranks)
print(f"\nQuestions scored: {len(ranks)}   Hit@5: {hit5:.2f}   MRR: {mrr:.2f}")

label = outputs_file.replace("pipeline_outputs", "").replace(".json", "").strip("_") or "default"
with open(f"retrieval_metrics_{label}.json", "w", encoding="utf-8") as f:
    json.dump({"source_file": outputs_file, "n": len(ranks), "hit_at_5": round(hit5, 3),
               "mrr": round(mrr, 3), "per_question": per_question}, f, indent=2)
print(f"Saved retrieval_metrics_{label}.json")
