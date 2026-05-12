import hashlib
import os


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
    print(f"[RAG] Storing skipped - using direct text: {pdf_name}")


def get_relevant_chunks(question: str, chat_id: str, pdf_name: str, top_k: int = 3) -> str:
    return ""