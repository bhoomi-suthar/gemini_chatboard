import hashlib
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from config import PINECONE_API_KEY, PINECONE_INDEX

embedder = SentenceTransformer("all-MiniLM-L6-v2")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


def chunk_text(text: str, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def embed_and_store_pdf(pdf_text, pdf_name, chat_id):
    chunks = chunk_text(pdf_text)
    vectors = []

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(
            f"{chat_id}_{pdf_name}_{i}".encode()
        ).hexdigest()

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

    index.upsert(vectors=vectors)
    print(f"Stored {len(vectors)} vectors in Pinecone")


def get_relevant_chunks(question, chat_id, pdf_name, top_k=3):
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
        print("score:", match.score)
        text += match.metadata["text"] + "\n\n"

    return text.strip()