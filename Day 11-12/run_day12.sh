#!/usr/bin/env bash
# Day 12: evaluate local, run + evaluate cloud, security probes, compare.
# Needs in THIS shell (from your Day 8 .env, never committed):
#   set -a; source "../Day 8/.env"; set +a      # or wherever your Day 8 .env is
#   export JUDGE_BASE_URL="$AZURE_OPENAI_ENDPOINT"   # must end in /openai/v1/
#   bash run_day12.sh            # everything
#   bash run_day12.sh security   # only the security probes (local + cloud)
#   bash run_day12.sh compare    # only compare.py
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
export PYTHONUNBUFFERED=1
step="${1:-all}"

: "${AZURE_OPENAI_API_KEY:?Set AZURE_OPENAI_API_KEY in this shell first (see top of this script)}"
: "${JUDGE_BASE_URL:?Set JUDGE_BASE_URL (your endpoint ending in /openai/v1/) first}"
unset LLM_BASE_URL LLM_API_KEY LLM_MODEL TOKEN_LIMIT_PARAM TEMPERATURE REASONING_EFFORT || true

# The cloud variables are passed per command, so they never leak into a local run.
cloud() {
  LLM_BASE_URL="$JUDGE_BASE_URL" LLM_API_KEY="$AZURE_OPENAI_API_KEY" \
  LLM_MODEL="gpt-5.6-luna" TOKEN_LIMIT_PARAM="max_completion_tokens" "$@"
}

if [[ "$step" == "all" || "$step" == "local" ]]; then
  if [[ ! -f pipeline_outputs_local.json ]]; then
    unrated=$(uv run python -c "import json; print(sum(r['passed'] is None for r in json.load(open('pipeline_outputs.json'))))")
    if [[ "$unrated" != "0" ]]; then
      echo "STOP: $unrated rows in pipeline_outputs.json have no 'passed' yet. Rate them first."; exit 1
    fi
    cp pipeline_outputs.json pipeline_outputs_local.json
  fi
  echo "== Evaluate local"
  uv run python eval_pipeline.py local 2>&1 | tee logs/10_eval_local.txt
  uv run python retrieval_metrics.py pipeline_outputs_local.json 2>&1 | tee logs/11_retrieval_metrics.txt
fi

if [[ "$step" == "all" || "$step" == "cloud" ]]; then
  echo "== Cloud test-set run (gpt-5.6-luna) -> pipeline_outputs_cloud.json"
  cloud uv run python pipeline.py --test-set pipeline_outputs_cloud.json 2>&1 | tee logs/12_cloud_test_set.txt
  echo "== Evaluate cloud"
  uv run python eval_pipeline.py cloud 2>&1 | tee logs/13_eval_cloud.txt
fi

if [[ "$step" == "all" || "$step" == "security" ]]; then
  echo "== Security probes"
  uv run python security_probe.py local 2>&1 | tee logs/14_security_local.txt
  cloud uv run python security_probe.py cloud 2>&1 | tee logs/15_security_cloud.txt
fi

if [[ "$step" == "all" || "$step" == "compare" ]]; then
  echo "== Compare"
  uv run python compare.py 2>&1 | tee logs/16_compare.txt
fi
echo "Done. Next: fill verdict/note in security_results_*.json, then write evaluation_report.md."
