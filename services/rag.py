from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX
import hashlib
import google.generativeai as genai
from config import GEMINI_API_KEY

# init pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(
    name=PINECONE_INDEX,
    host="rag-pdf-0wpd80f.svc.aped-4627-b74a.pinecone.io"
)

# init gemini
genai.configure(api_key=GEMINI_API_KEY)

def get_embedding(text: str) -> list:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text
    )
    return result["embedding"]

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def embed_and_store_pdf(pdf_text: str, pdf_name: str, chat_id: str):
    chunks = chunk_text(pdf_text)
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
    # upsert all at once
    index.upsert(vectors=vectors)

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