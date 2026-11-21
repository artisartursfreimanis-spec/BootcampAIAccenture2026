"""Exercise 1: compare local models on speed and quality across task types.

    uv run python benchmark.py                          # all models in MODELS
    uv run python benchmark.py qwen3.5:9b-q4_K_M        # only the models you name

Writes benchmark_results.json. Afterwards fill in quality_rating (1-5) and
rating_note by hand. Re-running overwrites the file, so rate last.
"""

import json
import sys
import time

from openai import OpenAI

import config

# Same quantisation (q4_K_M) and thinking off for all three, so the comparison is fair.
MODELS = ["qwen3.5:9b-q4_K_M", "qwen3.5:4b-q4_K_M", "qwen3.5:2b-q4_K_M"]

PROMPTS = [
    {"category": "factual",
     "prompt": "What causes tides on Earth? Answer in 2-3 sentences."},
    {"category": "reasoning",
     "prompt": "If a train travels 120 km in 1.5 hours, and then 80 km in 1 hour, what is the average "
               "speed for the entire journey? Show the calculation."},
    {"category": "summarization",
     "prompt": "Summarize the following in 2 sentences: Cloud computing has transformed how businesses operate "
               "by providing on-demand access to computing resources without the need for direct active "
               "management. The three main service models (IaaS, PaaS and SaaS) offer different levels of "
               "abstraction and management. IaaS provides virtualized computing resources, PaaS provides a "
               "platform for application development, and SaaS delivers complete applications over the "
               "internet. The shift to cloud has enabled organizations to reduce capital expenditure, improve "
               "scalability, and accelerate time to market for new products and services."},
    {"category": "structured_output",
     "prompt": 'List 3 European capitals. Respond ONLY with valid JSON: [{"city": "...", "country": "..."}]'},
    {"category": "code_generation",
     "prompt": "Write a Python function that takes a list of numbers and returns the second largest unique "
               "number, or None if there is none. Include a docstring."},
    {"category": "instruction_following",
     "prompt": "Name 5 programming languages. Format: numbered list, each with exactly one word of "
               "description. Example: 1. Python - versatile"},
    {"category": "rag_simulation",
     "prompt": 'Answer ONLY from the context. If the answer is not in it, say "I cannot find this information '
               'in the provided documents."\n\nContext: "Employees in eligible roles may work remotely for up '
               'to three (3) days per week, subject to manager approval. Employees still within their '
               'probationary period (six months) may work remotely for up to one (1) day per week with manager '
               'approval."\n\nQuestion: I started two months ago. How many days a week can I work from home?'},
    {"category": "rag_unanswerable",
     "prompt": 'Answer ONLY from the context. If the answer is not in it, say "I cannot find this information '
               'in the provided documents."\n\nContext: "NovaTech offers a one-time home office setup '
               'allowance of EUR 500 for employees approved for regular remote work."\n\n'
               'Question: How much is the monthly internet allowance for remote workers?'},
]


def chat(client: OpenAI, model: str, prompt: str):
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        reasoning_effort=config.REASONING_EFFORT,
        **{config.TOKEN_LIMIT_PARAM: config.MAX_TOKENS},
        **({"temperature": config.TEMPERATURE} if config.TEMPERATURE is not None else {}),
    )


def run_benchmark(client: OpenAI, model: str, item: dict) -> dict:
    start = time.time()
    response = chat(client, model, item["prompt"])
    elapsed = time.time() - start

    choice = response.choices[0]
    content = choice.message.content or ""
    usage = response.usage
    if not content.strip():
        print(f"\nWARNING: empty response from {model} (finish_reason={choice.finish_reason}) "
              f"on {item['category']}", file=sys.stderr)

    return {
        "model": model,
        "category": item["category"],
        "prompt": item["prompt"],
        "response": content,
        "thinking": config.REASONING_EFFORT != "none",
        "finish_reason": choice.finish_reason,
        "time_seconds": round(elapsed, 2),
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "tokens_per_second": round(usage.completion_tokens / elapsed, 1) if usage and usage.completion_tokens else None,
        "quality_rating": None,
        "rating_note": "",
    }


def main(models: list[str]):
    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
    results = []
    for model in models:
        print(f"\n{'=' * 60}\nModel: {model}\n{'=' * 60}")
        # Warm-up call (not saved): the first call also loads the model into memory,
        # which would make the first prompt look slow for reasons that are not the model's speed.
        t = time.time()
        try:
            chat(client, model, "Say hi.")
        except Exception as e:
            print(f"  SKIPPED: {model} did not answer ({e}). Is it pulled? ollama pull {model}")
            continue
        print(f"  warm-up / load: {time.time() - t:.1f} s")
        for item in PROMPTS:
            print(f"  {item['category']:<22}", end=" ", flush=True)
            r = run_benchmark(client, model, item)
            results.append(r)
            print(f"{r['time_seconds']:>6} s  {r['tokens_per_second'] or 'N/A':>6} tok/s  {r['finish_reason']}")

    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} rows to benchmark_results.json")

    # Per-model summary, computed from the rows that were just saved
    print(f"\n{'model':<22} {'avg s':>7} {'avg tok/s':>10} {'empty':>6}")
    for model in models:
        rows = [r for r in results if r["model"] == model]
        if not rows:
            continue
        avg_t = sum(r["time_seconds"] for r in rows) / len(rows)
        tps = [r["tokens_per_second"] for r in rows if r["tokens_per_second"]]
        empty = sum(1 for r in rows if not r["response"].strip())
        print(f"{model:<22} {avg_t:>7.2f} {(sum(tps) / len(tps) if tps else 0):>10.1f} {empty:>6}")
    print("\nNow open benchmark_results.json and fill in quality_rating (1-5) and rating_note by hand.")


if __name__ == "__main__":
    main(sys.argv[1:] or MODELS)
