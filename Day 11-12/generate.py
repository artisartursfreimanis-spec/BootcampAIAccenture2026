"""Generation: retrieved chunks + question -> answer from the LLM in config.py."""

import sys
import time

from openai import OpenAI

import config


def build_context(chunks: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {c['source']}, Page {c['page']}]\n{c['content']}" for c in chunks
    )


def generate_answer(query: str, chunks: list[dict]) -> dict:
    """Returns the answer together with the exact context the model saw and call metadata."""
    context = build_context(chunks)
    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)

    start = time.time()
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT.format(context=context)},
            {"role": "user", "content": query},
        ],
        reasoning_effort=config.REASONING_EFFORT,
        **{config.TOKEN_LIMIT_PARAM: config.MAX_TOKENS},
        **({"temperature": config.TEMPERATURE} if config.TEMPERATURE is not None else {}),
    )
    elapsed_ms = round((time.time() - start) * 1000)

    choice = response.choices[0]
    answer = choice.message.content or ""
    usage = response.usage

    if not answer.strip():
        print(f"WARNING: empty answer from {config.LLM_MODEL} "
              f"(finish_reason={choice.finish_reason}) for: {query[:60]}", file=sys.stderr)

    return {
        "query": query,
        "answer": answer,
        "context_used": context,
        "model": config.LLM_MODEL,
        "thinking": config.REASONING_EFFORT != "none",
        "finish_reason": choice.finish_reason,
        "generation_time_ms": elapsed_ms,
        "tokens_generated": usage.completion_tokens if usage else None,
        "prompt_tokens": usage.prompt_tokens if usage else None,
    }


if __name__ == "__main__":
    test_chunks = [{
        "content": "Employees in eligible roles may work remotely for up to three (3) days per week, "
                   "subject to manager approval.",
        "source": "company_handbook.pdf",
        "page": 4,
    }]
    r = generate_answer("How many days per week can I work from home?", test_chunks)
    print(f"Answer: {r['answer']}")
    print(f"Model: {r['model']} | thinking: {r['thinking']} | finish_reason: {r['finish_reason']}")
    print(f"Time: {r['generation_time_ms']} ms | prompt_tokens: {r['prompt_tokens']} | "
          f"tokens_generated: {r['tokens_generated']}")
