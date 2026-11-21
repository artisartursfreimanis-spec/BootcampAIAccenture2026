# Day 11-12 Capstone: Local Document Q&A (RAG)

A document Q&A service that runs fully on the local machine: PDFs → chunks → local embeddings
(`nomic-embed-text`) → ChromaDB → local LLM through Ollama's OpenAI-compatible API.
Day 12 evaluates it with DeepEval and compares it with a cloud model.

**Pipeline evaluated on Day 12:** my own pipeline (this folder), not the reference.
**AI assistant used:** Claude (Anthropic).

## Machine

Arch Linux, RTX 5080 (16 GB VRAM), 64 GB RAM, native Ollama (systemd service).

## Setup

```bash
# 1. Ollama (Linux install script, creates the systemd service)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Context window 8192 for the whole server
sudo systemctl edit ollama        # add the two lines below, save
#   [Service]
#   Environment="OLLAMA_CONTEXT_LENGTH=8192"
sudo systemctl restart ollama

# 3. Models (local tags only, no cloud tags)
ollama pull qwen3.5:9b-q4_K_M
ollama pull qwen3.5:4b-q4_K_M
ollama pull qwen3.5:2b-q4_K_M
ollama pull nomic-embed-text

# 4. Python project (Python 3.12, uv)
uv add openai chromadb langchain-text-splitters pypdf deepeval
```

## Run

| Step | Command | Writes |
|---|---|---|
| Benchmark (Exercise 1) | `uv run python benchmark.py` | `benchmark_results.json` |
| **Rebuild `chroma_db/`** | `uv run python ingest.py` | `chroma_db/` (not committed) |
| Look at the chunks | `uv run python ingest.py --preview 3` | terminal only |
| Chunk / top-K experiment | `uv run python chunk_experiment.py` | `chunk_experiment_results.json` |
| One question | `uv run python pipeline.py "your question"` | terminal only |
| Test set (Exercise 2) | `uv run python pipeline.py --test-set` | `pipeline_outputs.json` |

Or all Day 11 steps at once: `bash run_day11.sh` (also saves the terminal output in `logs/`).

## Day 12

```bash
set -a; source "<path to Day 8>/.env"; set +a
export JUDGE_BASE_URL="$AZURE_OPENAI_ENDPOINT"     # ends in /openai/v1/
bash run_day12.sh
```

| Step | Command | Writes |
|---|---|---|
| Copy rated local outputs | `cp pipeline_outputs.json pipeline_outputs_local.json` | |
| Evaluate local | `uv run python eval_pipeline.py local` | `eval_results_local.json` |
| Hit@5 / MRR (no judge) | `uv run python retrieval_metrics.py pipeline_outputs_local.json` | `retrieval_metrics_local.json` |
| Cloud run | 4 `LLM_*` variables + `uv run python pipeline.py --test-set pipeline_outputs_cloud.json` | `pipeline_outputs_cloud.json` |
| Evaluate cloud | `uv run python eval_pipeline.py cloud` | `eval_results_cloud.json` |
| Security | `uv run python security_probe.py local` / `cloud` | `security_results_*.json` |
| Compare | `uv run python compare.py` | `compare_output.md` |

`run_day12.sh` passes the cloud variables only to the cloud commands, so a later local run
cannot go to the cloud by accident.

## Files

| File | What it does |
|---|---|
| `config.py` | All settings; every provider setting is an environment variable |
| `ingest.py` | PDF → text (pypdf layout mode + cleanup) → chunks → embeddings → ChromaDB |
| `retrieve.py` | Query → top-K chunks with source, page, cosine score, time |
| `generate.py` | Chunks + question → answer, with the exact context, tokens, `finish_reason` |
| `pipeline.py` | retrieve + generate; `--test-set [file]` runs all of `test_questions.json` |
| `benchmark.py` | 3 models × 8 prompts, thinking off for all |
| `chunk_experiment.py` | Retrieval-only comparison of extraction mode, chunk size, top-K |
| `eval_pipeline.py` | Given Day 12 script, unchanged (judge `gpt-5.4-mini`) |
| `security_probe.py` | Given Day 12 script + own attacks (5 types, 6 rows) |
| `retrieval_metrics.py`, `compare.py` | Day 12 analysis |
| `test_questions.json` | 20 questions: 6 easy, 6 medium, 5 hard, 3 unanswerable |

Not committed: `.env`, `.venv/`, `chroma_db/`.
