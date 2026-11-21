#!/usr/bin/env bash
# Day 11: benchmark, ingest, chunk experiment, full test-set run. Everything local.
# Every step's terminal output is also saved in logs/ so it can be checked later.
#   bash run_day11.sh            # all steps
#   bash run_day11.sh pipeline   # only the test-set run (after you change something)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
export PYTHONUNBUFFERED=1
# Make sure nothing points to the cloud
unset LLM_BASE_URL LLM_API_KEY LLM_MODEL TOKEN_LIMIT_PARAM TEMPERATURE REASONING_EFFORT || true

MAIN_MODEL=$(uv run python -c "import config; print(config.LLM_MODEL)")
step="${1:-all}"

echo "== Ollama check" | tee logs/00_check.txt
{ ollama --version; curl -s http://localhost:11434/api/version; echo; ollama list; } 2>&1 | tee -a logs/00_check.txt

if [[ "$step" == "all" || "$step" == "benchmark" ]]; then
  echo "== Benchmark (Exercise 1)"
  uv run python benchmark.py 2>&1 | tee logs/01_benchmark.txt
fi

if [[ "$step" == "all" || "$step" == "ingest" ]]; then
  echo "== Ingest"
  uv run python ingest.py 2>&1 | tee logs/02_ingest.txt
  uv run python ingest.py --preview 2 > logs/02_chunk_preview.txt 2>&1
fi

if [[ "$step" == "all" || "$step" == "experiment" ]]; then
  echo "== Chunk / top-K experiment (retrieval only)"
  uv run python chunk_experiment.py 2>&1 | tee logs/03_chunk_experiment.txt
fi

if [[ "$step" == "all" || "$step" == "pipeline" ]]; then
  echo "== One question with the main model, then ollama ps while it is loaded"
  uv run python pipeline.py "How many days of paid time off do full-time employees get?" 2>&1 | tee logs/04_single_question.txt
  ollama ps 2>&1 | tee logs/04_ollama_ps.txt
  echo "== Full test set -> pipeline_outputs.json ($MAIN_MODEL)"
  uv run python pipeline.py --test-set 2>&1 | tee logs/05_test_set.txt
fi
echo "Done. Next: rate benchmark_results.json and pipeline_outputs.json by hand."
