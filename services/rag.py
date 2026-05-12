import hashlib
from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        print("✅ FastEmbed loaded")
    return _embedder


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
    embedder = get_embedder()
    chunks = chunk_text(pdf_text)
    vectors = []

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(
            f"{chat_id}_{pdf_name}_{i}".encode()
        ).hexdigest()
        try:
            vector = list(list(embedder.embed([chunk]))[0])
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
            print(f"Chunk {i} embedding failed: {e}")
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
        embedder = get_embedder()
        question_vector = list(list(embedder.embed([question]))[0])

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
            print("⚠️ RAG returned nothing, using fallback.")

        return relevant_text.strip()

    except Exception as e:
        print(f"RAG query error: {e}")
        return ""