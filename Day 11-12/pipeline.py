"""End-to-end RAG pipeline: question -> retrieve -> generate -> answer.

    uv run python pipeline.py "What is the PTO carryover limit?"     # one question
    uv run python pipeline.py --test-set                               # -> pipeline_outputs.json
    uv run python pipeline.py --test-set pipeline_outputs_cloud.json   # Day 12 cloud run, own file
"""

import json
import sys

import config
from generate import generate_answer
from retrieve import retrieve_chunks


def answer_question(query: str) -> dict:
    retrieval_result = retrieve_chunks(query)
    generation_result = generate_answer(query=query, chunks=retrieval_result["retrieved_chunks"])
    return {**generation_result, "retrieval": retrieval_result}


def run_test_set(test_file: str = "test_questions.json", output_file: str = "pipeline_outputs.json") -> list[dict]:
    with open(test_file, encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    for i, q in enumerate(questions, start=1):
        print(f"[{i}/{len(questions)}] {q['id']}: {q['question'][:70]}")
        out = answer_question(q["question"])
        chunks = out["retrieval"]["retrieved_chunks"]
        results.append({
            "id": q["id"],
            "question": q["question"],
            "expected_answer": q.get("expected_answer", ""),
            "actual_answer": out["answer"],
            "retrieved_context": [c["content"] for c in chunks],
            "context_sources": [{"source": c["source"], "page": c["page"], "score": c["relevance_score"]}
                                for c in chunks],
            "model": out["model"],
            "thinking": out["thinking"],
            "finish_reason": out["finish_reason"],
            "embedding_model": out["retrieval"]["embedding_model"],
            "chunk_size_chars": config.CHUNK_SIZE,
            "top_k": out["retrieval"]["top_k"],
            "prompt_tokens": out["prompt_tokens"],
            "tokens_generated": out["tokens_generated"],
            "retrieval_time_ms": out["retrieval"]["retrieval_time_ms"],
            "generation_time_ms": out["generation_time_ms"],
            "passed": None,
            "rating_note": "",
        })
        print(f"    -> {out['answer'][:100]!r} ({out['generation_time_ms']} ms, {out['finish_reason']})")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    empty = [r["id"] for r in results if not r["actual_answer"].strip()]
    print(f"\nSaved {len(results)} rows to {output_file}")
    if empty:
        print(f"WARNING: {len(empty)} empty answers: {', '.join(empty)}")
    print("Fill in passed (true/false) and rating_note by hand. Re-running overwrites the file.")
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-set":
        run_test_set(output_file=sys.argv[2] if len(sys.argv) > 2 else "pipeline_outputs.json")
    else:
        query = " ".join(sys.argv[1:]) or "What is the remote work policy?"
        r = answer_question(query)
        print(f"\nQuestion: {r['query']}\nAnswer: {r['answer']}\n")
        print(f"Retrieval: {len(r['retrieval']['retrieved_chunks'])} chunks in {r['retrieval']['retrieval_time_ms']} ms")
        print(f"Generation: {r['generation_time_ms']} ms ({r['model']}, finish_reason={r['finish_reason']}, "
              f"prompt_tokens={r['prompt_tokens']})")
        for i, c in enumerate(r["retrieval"]["retrieved_chunks"], start=1):
            print(f"  {i}. {c['source']} p.{c['page']} (score {c['relevance_score']})")
