from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from config import PINECONE_API_KEY, PINECONE_INDEX
import hashlib

# load embedding model once
embedder = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

# init pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(
    name=PINECONE_INDEX,
    host="rag-pdf-0wpd80f.svc.aped-4627-b74a.pinecone.io"
)


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
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
    """Chunk PDF text, embed, and store in Pinecone."""
    chunks = chunk_text(pdf_text)
    
    for i, chunk in enumerate(chunks):
        # unique id per chunk
        chunk_id = hashlib.md5(f"{chat_id}_{pdf_name}_{i}".encode()).hexdigest()
        
        # embed the chunk
        vector = embedder.encode(chunk).tolist()
        
        # store in pinecone with metadata
        index.upsert(vectors=[{
            "id": chunk_id,
            "values": vector,
            "metadata": {
                "chat_id": chat_id,
                "pdf_name": pdf_name,
                "chunk_index": i,
                "text": chunk
            }
        }])


def get_relevant_chunks(question: str, chat_id: str, pdf_name: str, top_k: int = 3) -> str:
    """Find most relevant PDF chunks for a question."""
    # embed the question
    question_vector = embedder.encode(question).tolist()
    
    # search pinecone for similar chunks from this specific pdf
    results = index.query(
        vector=question_vector,
        top_k=top_k,
        filter={
            "chat_id": {"$eq": chat_id},
            "pdf_name": {"$eq": pdf_name}
        },
        include_metadata=True
    )
    
    # combine top chunks
    relevant_text = ""
    for match in results.matches:
        relevant_text += match.metadata["text"] + "\n\n"
    
    return relevant_text.strip()