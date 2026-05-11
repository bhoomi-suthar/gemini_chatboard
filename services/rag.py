import os
import hashlib
import google.generativeai as genai
from pinecone import Pinecone

# hardcoded fallback so it always works
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_5oGKzU_RuTirbZNh9517tL8jbPsLRvkTfPywRb87BTPzue1aebiXDXcnrUjbV6YLcyUHPW")
PINECONE_HOST = os.getenv("PINECONE_HOST", "rag-pdf-0wpd80f.svc.aped-4627-b74a.pinecone.io")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "rag-pdf")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBF0EwG86ehckHju1D2qVVdS1o18hBAHdQ")

genai.configure(api_key=GEMINI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(name=PINECONE_INDEX, host=PINECONE_HOST)


def get_embedding(text: str) -> list:
    result = genai.embed_content(
        model="models/embedding-001",
        content=text
    )
    return result["embedding"]


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(' '.join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def embed_and_store_pdf(pdf_text: str, pdf_name: str, chat_id: str):
    print(f"[RAG] Storing PDF: {pdf_name}, chat: {chat_id}")
    chunks = chunk_text(pdf_text)
    print(f"[RAG] Total chunks: {len(chunks)}")
    vectors = []
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{chat_id}_{pdf_name}_{i}".encode()).hexdigest()
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
    index.upsert(vectors=vectors)
    print(f"[RAG] Upserted {len(vectors)} vectors successfully")


def get_relevant_chunks(question: str, chat_id: str, pdf_name: str, top_k: int = 3) -> str:
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
        relevant_text += match.metadata["text"] + "\n\n"
    return relevant_text.strip()