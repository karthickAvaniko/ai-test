import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from config import get_settings

settings = get_settings()

# ── Embedding Model (lazy load) ──────────────────────────
_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cuda"
        )
    return _embed_model

# ── ChromaDB (lazy load) ─────────────────────────────────
_chroma_client = None
_collections   = {}

def get_chroma():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=settings.VECTOR_DB_PATH
        )
    return _chroma_client

def get_collection(name: str):
    global _collections
    if name not in _collections:
        client = get_chroma()
        _collections[name] = client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )
    return _collections[name]

# ── Generate Embeddings ──────────────────────────────────
def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embed_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True
    )
    return embeddings.tolist()

# ── Store Documents ──────────────────────────────────────
def store_documents(
    texts: List[str],
    api_key: str,
    doc_id: str,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    try:
        collection = get_collection(f"user_{api_key[:8]}")
        embeddings = embed_texts(texts)

        ids = [
            f"{doc_id}_chunk_{i}"
            for i in range(len(texts))
        ]

        meta_list = []
        for i, text in enumerate(texts):
            m = {
                "doc_id":    doc_id,
                "chunk_id":  i,
                "api_key":   api_key[:8],
                "text_hash": hashlib.md5(text.encode()).hexdigest()
            }
            if metadata:
                m.update(metadata)
            meta_list.append(m)

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=meta_list
        )

        return {
            "success":       True,
            "stored_chunks": len(texts),
            "doc_id":        doc_id
        }

    except Exception as e:
        return {
            "success": False,
            "error":   str(e)
        }

# ── Search Similar ───────────────────────────────────────
def search_similar(
    query: str,
    api_key: str,
    top_k: int = 5,
    doc_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    try:
        collection = get_collection(f"user_{api_key[:8]}")
        query_embedding = embed_texts([query])[0]

        where = {"doc_id": doc_id} if doc_id else None

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        hits = []
        for i in range(len(results["documents"][0])):
            hits.append({
                "text":       results["documents"][0][i],
                "metadata":   results["metadatas"][0][i],
                "similarity": round(1 - results["distances"][0][i], 3)
            })

        return hits

    except Exception as e:
        return []

# ── Delete Documents ─────────────────────────────────────
def delete_documents(api_key: str, doc_id: str) -> Dict[str, Any]:
    try:
        collection = get_collection(f"user_{api_key[:8]}")
        collection.delete(where={"doc_id": doc_id})
        return {"success": True, "doc_id": doc_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── List Documents ───────────────────────────────────────
def list_documents(api_key: str) -> List[str]:
    try:
        collection = get_collection(f"user_{api_key[:8]}")
        results    = collection.get(include=["metadatas"])
        doc_ids    = list(set(
            m["doc_id"] for m in results["metadatas"]
        ))
        return doc_ids
    except:
        return []
