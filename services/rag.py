import hashlib
from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Lazy load embedder (important for Render)
embedder = None


def get_embedder():
    global embedder
    if embedder is None:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Embedder loaded")
    return embedder


def chunk_text(text: str, chunk_size=300, overlap=50):
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


def embed_and_store_pdf(pdf_text, pdf_name, chat_id):
    embedder = get_embedder()   # load model only when needed
    chunks = chunk_text(pdf_text)
    vectors = []

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(
            f"{chat_id}_{pdf_name}_{i}".encode()
        ).hexdigest()

        try:
            vector = embedder.encode(chunk).tolist()

            vectors.append({
                "id": chunk_id,
                "values": vector,
                "metadata": {
                    "chat_id": chat_id,
                    "pdf_name": pdf_name,
                    "text": chunk
                }
            })

        except Exception as e:
            print(f"Chunk embedding failed: {e}")

    if vectors:
        index.upsert(vectors=vectors)
        print(f"✅ Stored {len(vectors)} vectors in Pinecone")
    else:
        print("❌ No vectors stored")


def get_relevant_chunks(question, chat_id, pdf_name, top_k=3):
    embedder = get_embedder()   # load model only when needed

    try:
        question_vector = embedder.encode(question).tolist()

        results = index.query(
            vector=question_vector,
            top_k=top_k,
            include_metadata=True,
            filter={
                "chat_id": {"$eq": chat_id},
                "pdf_name": {"$eq": pdf_name}
            }
        )

        text = ""

        for match in results.matches:
            print(f"score: {match.score}")
            text += match.metadata["text"] + "\n\n"

        return text.strip()

    except Exception as e:
        print(f"RAG query failed: {e}")
        return ""