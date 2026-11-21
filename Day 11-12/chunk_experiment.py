"""Retrieval-only experiment: which extraction mode, chunk size and top-K find the evidence?

No LLM is called, only the local embedding model, so it is fast and gives the same result
on every run. For each setting it builds a throw-away in-memory ChromaDB collection and checks,
for every answerable test question, whether the retrieved chunks contain the evidence text the
answer needs (EVIDENCE below). Writes chunk_experiment_results.json.

    uv run python chunk_experiment.py
"""

import json
import re

import chromadb

import config
from ingest import chunk_documents, embed_texts, load_documents

# Settings to compare: (extraction mode, chunk size in characters, overlap in characters)
SETTINGS = [
    ("plain", 512, 50),
    ("layout", 256, 25),
    ("layout", 512, 50),
    ("layout", 1000, 100),
    ("layout", 1500, 150),
]
TOP_KS = [3, 5, 8]

# Text that must appear in the retrieved chunks for the question to be answerable.
# Questions with two strings need both (the contradiction questions need both sources).
EVIDENCE = {
    "q01": ["twenty-five (25) days"],
    "q02": ["allowance of €500"],
    "q03": ["within four (4) hours"],
    "q04": ["15% discount"],
    "q05": ["14-day free trial"],
    "q06": ["gross churn rate was 3.2%"],
    "q07": ["Recovery Point Objective"],
    "q08": ["Total at-risk ARR"],
    "q09": ["HubSpot 3-year TCO"],
    "q10": ["EUR 780K"],
    "q11": ["superset"],
    "q12": ["Total Customers"],
    "q13": ["released on February 12", "shipped January 28"],
    "q14": ["rotation is required every ninety", "90 days to 180 days"],
    "q15": ["dpo@novatech.io", "dpo@novatech-solutions.com"],
    "q16": ["98.0%"],
    "q17": ["4 days remote per week"],
}


def norm(text: str) -> str:
    # Lower case, single spaces, and drop the "NovaT ech" split that pypdf's plain mode produces
    return re.sub(r"\s+", " ", text.replace("|", " ")).lower()


def main():
    with open("test_questions.json", encoding="utf-8") as f:
        questions = [q for q in json.load(f) if q["id"] in EVIDENCE]
    query_vectors = embed_texts([q["question"] for q in questions])

    results = []
    for mode, size, overlap in SETTINGS:
        config.EXTRACTION_MODE = mode
        chunks = chunk_documents(load_documents(), chunk_size=size, chunk_overlap=overlap)

        # Sanity check: evidence that does not exist in ANY chunk cannot be retrieved
        all_text = [norm(c["content"]) for c in chunks]
        missing = [(qid, e) for qid, ev in EVIDENCE.items() for e in ev
                   if not any(norm(e) in t for t in all_text)]
        if missing:
            print(f"  note: evidence split across chunks or missing in this setting: {missing}")

        collection = chromadb.EphemeralClient().create_collection(
            name=f"exp_{mode}_{size}", metadata={"hnsw:space": "cosine"})
        vectors = embed_texts([c["content"] for c in chunks])
        for i in range(0, len(chunks), 100):
            part = chunks[i:i + 100]
            collection.add(ids=[c["id"] for c in part], documents=[c["content"] for c in part],
                           embeddings=vectors[i:i + 100])

        hits = collection.query(query_embeddings=query_vectors, n_results=max(TOP_KS),
                                include=["documents"])["documents"]
        for k in TOP_KS:
            per_q = {}
            for q, docs in zip(questions, hits):
                found = " ".join(norm(d) for d in docs[:k])
                per_q[q["id"]] = sum(norm(e) in found for e in EVIDENCE[q["id"]]) / len(EVIDENCE[q["id"]])
            row = {
                "extraction_mode": mode,
                "chunk_size_chars": size,
                "chunk_overlap_chars": overlap,
                "top_k": k,
                "n_chunks": len(chunks),
                "avg_chunk_chars": round(sum(len(c["content"]) for c in chunks) / len(chunks)),
                "context_chars_at_k": k * round(sum(len(c["content"]) for c in chunks) / len(chunks)),
                "evidence_recall": round(sum(per_q.values()) / len(per_q), 3),
                "per_question": per_q,
            }
            results.append(row)
            print(f"{mode:<7} size={size:<5} k={k}  chunks={len(chunks):<4} "
                  f"evidence_recall={row['evidence_recall']:.3f}")

    with open("chunk_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nSaved chunk_experiment_results.json")


if __name__ == "__main__":
    main()
