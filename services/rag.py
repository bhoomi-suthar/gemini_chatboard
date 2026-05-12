import hashlib
import os
from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX, GEMINI_API_KEY
import google.generativeai as genai

# init gemini embedding
genai.configure(api_key=GEMINI_API_KEY)

# init pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


def get_embedding(text: str) -> list:
    """Get embedding using Gemini text-embedding-004 (768 dims)."""
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document"
    )
    return result["embedding"]


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    """Split text into overlapping chunks."""
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
    """Chunk PDF, embed each chunk, store in Pinecone."""
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
        except Exception as e:
            print(f"Embedding error on chunk {i}: {e}")
            continue

    # upsert in batches of 50
    batch_size = 50
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        try:
            index.upsert(vectors=batch)
            print(f"✅ Stored {len(batch)} chunks in Pinecone")
        except Exception as e:
            print(f"Pinecone upsert error: {e}")


def get_relevant_chunks(question: str, chat_id: str, pdf_name: str, top_k: int = 3) -> str:
    """Find most relevant chunks for a question."""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=question,
            task_type="retrieval_query"
        )
        question_vector = result["embedding"]

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
            score = match.score
            chunk = match.metadata.get("text", "")
            print(f"✅ RAG match — score: {score:.3f} | chunk: {chunk[:80]}")
            relevant_text += chunk + "\n\n"

        return relevant_text.strip()

    except Exception as e:
        print(f"RAG query error: {e}")
        return ""