# Decision Log: Local RAG Pipeline

<!-- Written by me (rule 5). Every number: name the file and the id / model next to it. -->

## Machine
- **Hardware:** Arch Linux, [CPU], 64 GB RAM, RTX 5080 16 GB VRAM, native Ollama [version from logs/00_check.txt]
- **`ollama ps` with my main model loaded:** (from logs/04_ollama_ps.txt)
```
[paste]
```

## Model Selection
- **Chosen LLM:** [tag]
- **Thinking:** [on/off, why]
- **Why:** [benchmark_results.json: tok/s, time, your ratings per model]
- **What I considered but rejected:** [...]

## Embedding Model
- **Chosen:** nomic-embed-text, [dimensions, printed by ingest.py in logs/02_ingest.txt]
- **Why:** [...]

## Parsing
- **Extractor:** [pypdf plain vs layout; what a table page looked like: logs/02_chunk_preview.txt]

## Chunking Strategy
- **Chunk size:** [value] characters
- **Overlap:** [value] characters
- **Why:** [chunk_experiment_results.json: evidence_recall per setting]

## Retrieval Configuration
- **Top-K:** [value]
- **Context window:** [CONTEXT from ollama ps]; prompt_tokens observed: [range from pipeline_outputs.json]
- **Why:** [chunk_experiment_results.json, k = 3 / 5 / 8]

## Observations
- **What worked well:** [ids from pipeline_outputs.json]
- **What failed:** [ids, why]
- **Traps I hit:** [...]
- **Local vs cloud expectations:** [...]

## If I Had More Time / Better Hardware
- [...]
