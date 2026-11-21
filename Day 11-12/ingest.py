"""Ingestion: load PDFs, clean the text, chunk, embed locally, store in ChromaDB.

    uv run python ingest.py                 # rebuilds chroma_db/ from documents/
    uv run python ingest.py --preview 3     # print the first 3 chunks of every PDF, no embedding
"""

import hashlib
import os
import re
import sys

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pypdf import PdfReader

import config


def clean_text(text: str) -> str:
    """Tidy pypdf layout-mode output.

    Layout mode pads table columns with long runs of spaces. Three or more spaces
    become " | ", so a row reads "Starter | 99.5% | ~3 hours 39 minutes".
    Blank lines between two table rows are dropped, so a table stays together
    in one chunk instead of being split at every row.
    """
    lines = [re.sub(r" {3,}", " | ", line.strip()) for line in text.splitlines()]
    kept = []
    for i, line in enumerate(lines):
        if line == "" and kept and " | " in kept[-1]:
            nxt = next((l for l in lines[i + 1:] if l), "")
            if " | " in nxt:
                continue
        kept.append(line)
    cleaned = "\n".join(kept)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def extract_page(page) -> str:
    if config.EXTRACTION_MODE == "layout":
        return clean_text(page.extract_text(extraction_mode="layout"))
    return page.extract_text()


def load_documents(documents_dir: str = config.DOCUMENTS_DIR) -> list[dict]:
    documents = []
    for filename in sorted(os.listdir(documents_dir)):
        if not filename.lower().endswith(".pdf"):
            continue
        reader = PdfReader(os.path.join(documents_dir, filename))
        for page_number, page in enumerate(reader.pages, start=1):
            documents.append({
                "content": extract_page(page),
                "source": filename,
                "page": page_number,
            })
    print(f"Loaded {len(documents)} pages from {documents_dir} (extraction: {config.EXTRACTION_MODE})")
    return documents


def chunk_documents(documents: list[dict], chunk_size: int = config.CHUNK_SIZE,
                    chunk_overlap: int = config.CHUNK_OVERLAP) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for doc in documents:
        for i, text in enumerate(splitter.split_text(doc["content"])):
            # Stable ID: the same chunk always gets the same ID, so re-ingesting never duplicates.
            chunk_id = hashlib.md5(f"{doc['source']}:{doc['page']}:{i}".encode()).hexdigest()
            chunks.append({
                "id": chunk_id,
                "content": text,
                "source": doc["source"],
                "page": doc["page"],
                "chunk_index": i,
            })
    print(f"Created {len(chunks)} chunks (size={chunk_size} characters, overlap={chunk_overlap} characters)")
    return chunks


def embed_texts(texts: list[str], batch_size: int = 20) -> list[list[float]]:
    client = OpenAI(base_url=config.EMBEDDING_BASE_URL, api_key=config.EMBEDDING_API_KEY)
    vectors = []
    for i in range(0, len(texts), batch_size):
        response = client.embeddings.create(model=config.EMBEDDING_MODEL, input=texts[i:i + batch_size])
        vectors.extend(item.embedding for item in response.data)
    return vectors


def embed_and_store(chunks: list[dict]) -> chromadb.Collection:
    """Deletes and recreates the collection, so a re-run never duplicates chunks."""
    chroma_client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    try:
        chroma_client.delete_collection(config.COLLECTION_NAME)
    except chromadb.errors.NotFoundError:
        pass
    # cosine space: then 1 - distance is a similarity between 0 and 1
    collection = chroma_client.create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["content"] for c in chunks]
    embeddings = embed_texts(texts)
    print(f"Embedded {len(embeddings)} chunks with {config.EMBEDDING_MODEL} ({len(embeddings[0])} dimensions)")

    # Embeddings are always passed in, so ChromaDB never embeds with its own default model.
    batch = 100
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        collection.add(
            ids=[c["id"] for c in part],
            documents=[c["content"] for c in part],
            embeddings=embeddings[i:i + batch],
            metadatas=[{"source": c["source"], "page": c["page"], "chunk_index": c["chunk_index"]} for c in part],
        )
    print(f"Stored {collection.count()} chunks in ChromaDB at {config.CHROMA_PERSIST_DIR}")
    return collection


def ingest(documents_dir: str = config.DOCUMENTS_DIR) -> chromadb.Collection:
    documents = load_documents(documents_dir)
    chunks = chunk_documents(documents)
    return embed_and_store(chunks)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        all_chunks = chunk_documents(load_documents())
        shown = {}
        for c in all_chunks:
            if shown.get(c["source"], 0) < n:
                shown[c["source"]] = shown.get(c["source"], 0) + 1
                print(f"\n--- {c['source']} p.{c['page']} chunk {c['chunk_index']} ({len(c['content'])} chars) ---")
                print(c["content"])
    else:
        ingest()
