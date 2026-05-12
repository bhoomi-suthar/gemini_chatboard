import hashlib
import os
import requests as http_requests
from pinecone import Pinecone

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "gemini-chat-pdf")
PINECONE_HOST = os.getenv("PINECONE_HOST", "")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(name=PINECONE_INDEX, host=PINECONE_HOST)


def get_embedding(text: str) -> list:
    url = f"https://generativelanguage.googleapis.com/v1/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]}
    }
    response = http_requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["embedding"]["values"]


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
    print(f"[RAG] Storing: {pdf_name}")
    chunks = chunk_text(pdf_text)
    vectors = []
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{chat_id}_{pdf_name}_{i}".encode()).hexdigest()
        try:
            vector = get_embedding(chunk)
            vectors.append({
                "id": chunk_id,
                "values": vector,
                "metadata": {
                    "chat_id": chat_id,
                    "pdf_name": pdf_name,
                    "chunk_index": i,
                    "text": chunk
                }
            })
        except Exception as e:
            print(f"Chunk {i} failed: {e}")
            continue

    for i in range(0, len(vectors), 50):
        batch = vectors[i:i + 50]
        try:
            index.upsert(vectors=batch)
            print(f"[RAG] Stored {len(batch)} chunks")
        except Exception as e:
            print(f"Pinecone upsert error: {e}")


def get_relevant_chunks(question: str, chat_id: str, pdf_name: str, top_k: int = 3) -> str:
    try:
        question_vector = get_embedding(question)
        results = index.query(
            vector=question_vector,
            top_k=top_k,
            filter={
                "chat_id": {"$eq": chat_id},
                "pdf_name": {"$eq": pdf_name}
            },
            include_metadata=True
        )
        relevant_text = ""
        for match in results.matches:
            relevant_text += match.metadata.get("text", "") + "\n\n"
        return relevant_text.strip()
    except Exception as e:
        print(f"RAG query error: {e}")
        return ""