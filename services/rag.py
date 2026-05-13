import hashlib
import cohere
from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX, COHERE_API_KEY

co = cohere.Client(COHERE_API_KEY)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def get_embedding(text):
    response = co.embed(
        texts=[text],
        model="embed-english-v3.0",
        input_type="search_document"
    )
    return response.embeddings[0]


def embed_and_store_pdf(pdf_text, pdf_name, chat_id):
    chunks = chunk_text(pdf_text)
    vectors = []

    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)

        chunk_id = hashlib.md5(
            f"{chat_id}_{pdf_name}_{i}".encode()
        ).hexdigest()

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
    print(f"Stored {len(vectors)} vectors")


def get_relevant_chunks(question, chat_id, pdf_name, top_k=3):
    query_vector = get_embedding(question)

    results = index.query(
        vector=query_vector,
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