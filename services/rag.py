import hashlib
import os

# store chunks in memory per session
_pdf_store = {}

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def embed_and_store_pdf(pdf_text: str, pdf_name: str, chat_id: str):
    key = f"{chat_id}_{pdf_name}"
    _pdf_store[key] = chunk_text(pdf_text)
    print(f"[RAG] Stored {len(_pdf_store[key])} chunks for {pdf_name}")

def get_relevant_chunks(question: str, chat_id: str, pdf_name: str, top_k: int = 3) -> str:
    key = f"{chat_id}_{pdf_name}"
    chunks = _pdf_store.get(key, [])
    if not chunks:
        return ""

    # score each chunk by keyword matches
    question_words = set(question.lower().split())
    scored = []
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        score = len(question_words & chunk_words)
        scored.append((score, chunk))

    # sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # return top chunks
    top_chunks = [c for _, c in scored[:top_k] if _ > 0]
    if not top_chunks:
        return chunks[0] if chunks else ""

    return "\n\n".join(top_chunks)