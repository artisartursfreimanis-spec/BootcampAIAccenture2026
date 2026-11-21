### Quality: qwen3.5:9b-q4_K_M (local) vs gpt-5.6-luna (cloud), judge scores, mean ± 2×SE

| Metric | n | Local | Cloud | Cloud − local (paired) | Verdict |
|---|---|---|---|---|---|
| Faithfulness | 20 | 0.77 ± 0.13 | 0.80 ± 0.16 | +0.02 ± 0.13 | no clear difference |
| Answer Relevancy | 20 | 0.97 ± 0.04 | 0.97 ± 0.05 | +0.01 ± 0.03 | no clear difference |
| Contextual Relevancy | 20 | 0.35 ± 0.11 | 0.36 ± 0.11 | +0.01 ± 0.03 | no clear difference |
| Contextual Recall | 20 | 0.68 ± 0.18 | 0.68 ± 0.18 | -0.00 ± 0.01 | no clear difference |
| Contextual Precision | 20 | 0.82 ± 0.14 | 0.90 ± 0.07 | +0.08 ± 0.14 | no clear difference |

### Cost and robustness per run (from pipeline_outputs_*.json)

| Run | Model | Median gen. time (s) | Slowest (s) | Avg completion tokens | Empty / failed | Unanswerable refused |
|---|---|---|---|---|---|---|
| local | qwen3.5:9b-q4_K_M | 0.76 | 2.77 | 109 | 0 | 3 of 3 |
| cloud | gpt-5.6-luna | 1.38 | 1.92 | 47 | 0 | 3 of 3 |

### Per question (Faithfulness / Answer Relevancy)

| id | Local F | Cloud F | Local AR | Cloud AR |
|---|---|---|---|---|
| q01 | 1.00 | 1.00 | 1.00 | 1.00 |
| q02 | 1.00 | 0.67 | 1.00 | 1.00 |
| q03 | 0.50 | 1.00 | 1.00 | 1.00 |
| q04 | 0.33 | 1.00 | 1.00 | 1.00 |
| q05 | 0.83 | 1.00 | 1.00 | 1.00 |
| q06 | 1.00 | 1.00 | 1.00 | 1.00 |
| q07 | 0.89 | 1.00 | 1.00 | 1.00 |
| q08 | 0.67 | 1.00 | 0.95 | 1.00 |
| q09 | 1.00 | 1.00 | 1.00 | 1.00 |
| q10 | 0.83 | 0.57 | 1.00 | 1.00 |
| q11 | 0.89 | 0.83 | 1.00 | 1.00 |
| q12 | 0.89 | 1.00 | 1.00 | 1.00 |
| q13 | 1.00 | 1.00 | 1.00 | 1.00 |
| q14 | 1.00 | 1.00 | 0.67 | 0.50 |
| q15 | 1.00 | 1.00 | 1.00 | 1.00 |
| q16 | 0.73 | 0.83 | 1.00 | 1.00 |
| q17 | 1.00 | 1.00 | 0.75 | 1.00 |
| q18 | 0.00 | 0.00 | 1.00 | 1.00 |
| q19 | 0.67 | 0.00 | 1.00 | 1.00 |
| q20 | 0.25 | 0.00 | 1.00 | 1.00 |

A paired range that includes zero means the runs have not shown a difference. Retrieval is identical in both runs, so any gap in the Contextual metrics is judge noise.
