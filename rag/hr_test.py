from rag.document_loader import build_chunks
from rag.vector_store import VectorStore

config = {
    "vector_store": {
        "faiss_index_path": "artifacts/hr/files.index",
        "vectorizer_path": "artifacts/hr/vectorizer.pkl",
        "chunks_metadata_path": "artifacts/hr/chunks.pkl",
    }
}

chunks = build_chunks("rag/hr_knowledge_base", chunk_size=1000, chunk_overlap=100)
print("Chunks:", len(chunks))
print("Longest chunk:", max(len(c["text"]) for c in chunks))

store = VectorStore(config)
store.build(chunks)

vectorizer, index, saved_chunks = store.load()
print("Dimension:", index.d)
print("Total vectors:", index.ntotal)


from sklearn.preprocessing import normalize
import faiss

query = "How many casual leaves are allowed in a year?"
q = vectorizer.transform([query]).toarray().astype("float32")
faiss.normalize_L2(q)

scores, ids = index.search(q, 3)
for score, i in zip(scores[0], ids[0]):
    print(round(float(score), 3), saved_chunks[i]["chunk_id"], saved_chunks[i]["text"][:120])