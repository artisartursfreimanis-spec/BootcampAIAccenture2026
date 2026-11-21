"""Local vs cloud comparison for the Day 12 report.

Reads eval_results_local.json, eval_results_cloud.json, pipeline_outputs_local.json and
pipeline_outputs_cloud.json and prints markdown tables (paste them into evaluation_report.md):

  1. per metric: n, local mean ± 2×SE, cloud mean ± 2×SE, paired difference (cloud - local)
     ± 2×SE, and a verdict ("no clear difference" if the paired range includes zero)
  2. per run: median and slowest generation time, average completion tokens, empty/failed answers,
     refusals on the unanswerable questions
  3. per question: the Faithfulness and AnswerRelevancy scores side by side

    uv run python compare.py              # prints, and also saves compare_output.md
"""

import json
import statistics

METRICS = ["Faithfulness", "Answer Relevancy", "Contextual Relevancy",
           "Contextual Recall", "Contextual Precision"]
REFUSAL = "cannot find this information"


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def mean_2se(values: list[float]) -> tuple[float, float]:
    if not values:
        return float("nan"), float("nan")
    if len(values) < 2:
        return values[0], float("nan")
    return statistics.mean(values), 2 * statistics.stdev(values) / len(values) ** 0.5


def scores(rows: list[dict]) -> dict:
    """{question id: {metric name: score or None}}"""
    return {r["id"]: {m: (v.get("score") if not v.get("error") else None) for m, v in r["metrics"].items()}
            for r in rows}


def fmt(m: float, e: float) -> str:
    return f"{m:.2f} ± {e:.2f}" if e == e else f"{m:.2f}"


def main():
    lines = []
    out = lines.append

    ev_local, ev_cloud = scores(load("eval_results_local.json")), scores(load("eval_results_cloud.json"))
    po_local, po_cloud = load("pipeline_outputs_local.json"), load("pipeline_outputs_cloud.json")
    model_local = po_local[0]["model"] if po_local else "local"
    model_cloud = po_cloud[0]["model"] if po_cloud else "cloud"

    # Metric names as DeepEval wrote them (falls back to the list above)
    names = sorted({m for row in ev_local.values() for m in row} | {m for row in ev_cloud.values() for m in row})
    names = [m for m in METRICS if m in names] + [m for m in names if m not in METRICS]

    out(f"### Quality: {model_local} (local) vs {model_cloud} (cloud), judge scores, mean ± 2×SE\n")
    out("| Metric | n | Local | Cloud | Cloud − local (paired) | Verdict |")
    out("|---|---|---|---|---|---|")
    for m in names:
        ids = [i for i in ev_local if i in ev_cloud
               and ev_local[i].get(m) is not None and ev_cloud[i].get(m) is not None]
        a = [ev_local[i][m] for i in ids]
        b = [ev_cloud[i][m] for i in ids]
        (ma, ea), (mb, eb) = mean_2se(a), mean_2se(b)
        md, ed = mean_2se([y - x for x, y in zip(a, b)])
        if ed != ed:
            verdict = "too few questions"
        elif md - ed <= 0 <= md + ed:
            verdict = "no clear difference"
        else:
            verdict = "cloud higher" if md > 0 else "local higher"
        out(f"| {m} | {len(ids)} | {fmt(ma, ea)} | {fmt(mb, eb)} | {md:+.2f} ± {ed:.2f} | {verdict} |")

    out("\n### Cost and robustness per run (from pipeline_outputs_*.json)\n")
    out("| Run | Model | Median gen. time (s) | Slowest (s) | Avg completion tokens | Empty / failed | "
        "Unanswerable refused |")
    out("|---|---|---|---|---|---|---|")
    with open("test_questions.json", encoding="utf-8") as f:
        unanswerable = {q["id"] for q in json.load(f) if q.get("type") == "unanswerable"}
    for label, rows in (("local", po_local), ("cloud", po_cloud)):
        times = [r["generation_time_ms"] / 1000 for r in rows if r.get("generation_time_ms") is not None]
        toks = [r["tokens_generated"] for r in rows if r.get("tokens_generated") is not None]
        bad = sum(1 for r in rows if not (r.get("actual_answer") or "").strip()
                  or r.get("finish_reason") not in ("stop", None))
        refused = sum(1 for r in rows if r["id"] in unanswerable and REFUSAL in r["actual_answer"].lower())
        out(f"| {label} | {rows[0]['model'] if rows else '-'} | "
            f"{statistics.median(times):.2f} | {max(times):.2f} | {statistics.mean(toks):.0f} | {bad} | "
            f"{refused} of {sum(1 for r in rows if r['id'] in unanswerable)} |")

    out("\n### Per question (Faithfulness / Answer Relevancy)\n")
    out("| id | Local F | Cloud F | Local AR | Cloud AR |")
    out("|---|---|---|---|---|")

    def s(d, i, m):
        v = d.get(i, {}).get(m)
        return "err" if v is None else f"{v:.2f}"
    for i in sorted(set(ev_local) | set(ev_cloud)):
        out(f"| {i} | {s(ev_local, i, 'Faithfulness')} | {s(ev_cloud, i, 'Faithfulness')} | "
            f"{s(ev_local, i, 'Answer Relevancy')} | {s(ev_cloud, i, 'Answer Relevancy')} |")

    out("\nA paired range that includes zero means the runs have not shown a difference. "
        "Retrieval is identical in both runs, so any gap in the Contextual metrics is judge noise.")

    text = "\n".join(lines)
    print(text)
    with open("compare_output.md", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("\nSaved compare_output.md")


if __name__ == "__main__":
    main()
