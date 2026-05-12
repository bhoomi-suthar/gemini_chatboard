import hashlib
import requests
import json
from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX, GEMINI_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


def get_embedding(text: str) -> list:
    """Use Gemini embedding via REST - v1beta works for embedding-001"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={GEMINI_API_KEY}"
    payload = {
        "model": "models/embedding-001",
        "content": {
            "parts": [{"text": text[:2000]}]
        }
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code == 200:
        return resp.json()["embedding"]["values"]
    raise Exception(f"Embed failed {resp.status_code}: {resp.text[:200]}")


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
    chunks = chunk_text(pdf_text)
    vectors = []

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(
            f"{chat_id}_{pdf_name}_{i}".encode()
        ).hexdigest()
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
            print(f"✅ Embedded chunk {i}")
        except Exception as e:
            print(f"Chunk {i} failed: {e}")
            continue

    for i in range(0, len(vectors), 50):
        batch = vectors[i:i + 50]
        try:
            index.upsert(vectors=batch)
            print(f"✅ Stored {len(batch)} chunks in Pinecone")
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
            chunk = match.metadata.get("text", "")
            print(f"✅ RAG score: {match.score:.3f} | {chunk[:80]}")
            relevant_text += chunk + "\n\n"

        if not relevant_text:
            print("⚠️ RAG returned nothing.")

        return relevant_text.strip()

    except Exception as e:
        print(f"RAG query error: {e}")
        return ""