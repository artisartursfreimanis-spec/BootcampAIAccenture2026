# AGENTS.md

Rules for any AI assistant working in this folder.

## The brief's rules
- **Local models only** inside the pipeline. Ollama tags without `cloud`. The cloud model
  (`gpt-5.6-luna`) is used only in the Day 12 comparison, through environment variables.
- **Numbers come from files.** Never write a number into `decision_log.md`, `evaluation_report.md`
  or this README by hand. Every number comes from a JSON file that the code wrote.
- **The assistant may write the script that measures, not the number.**
  `decision_log.md` and `evaluation_report.md` are based on my own answers and decisions.
- Hand ratings (`quality_rating`, `passed`, `verdict`, `rating_note`, `note`) are checked and approved by me.
- **Never read, print or commit `.env`.** Do not commit `chroma_db/` or `.venv/`.
- One step at a time: ingest, retrieve, generate, benchmark. Run and commit each step.

## How to run each script
```bash
uv run python ingest.py                       # rebuild chroma_db/
uv run python retrieve.py "question"          # check retrieval only
uv run python generate.py                     # check generation only (fixed test chunk)
uv run python pipeline.py "question"          # one question end to end
uv run python pipeline.py --test-set [file]   # all test questions
uv run python benchmark.py [model ...]        # Exercise 1
uv run python chunk_experiment.py             # retrieval experiment
uv run python eval_pipeline.py local|cloud    # Day 12 judge
uv run python security_probe.py local|cloud   # Day 12 attacks
uv run python compare.py                      # Day 12 local vs cloud
```

## The check after every change
1. `uv run python ingest.py` prints the same chunk count twice in a row (no duplicates).
2. `uv run python pipeline.py "How many days of paid time off do full-time employees get?"`
   gives a non-empty answer with `finish_reason=stop` and cites `company_handbook.pdf`.
3. Every chat call has `reasoning_effort` and the token cap under `config.TOKEN_LIMIT_PARAM`.
