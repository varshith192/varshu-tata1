"""
Hybrid RAG knowledge base: FAISS semantic search + BM25 keyword search fused with RRF.
Falls back to TF-IDF keyword search if FAISS unavailable.
"""
import os
import logging
from typing import List, Tuple, Dict, Any

from .documents import get_all_documents

logger = logging.getLogger("Stelos.RAG")

_vector_store = None
_tfidf_fallback = None
_bm25_index = None        # BM25Okapi index
_bm25_corpus: List[str] = []  # tokenised corpus parallel to _docs_cache
_docs_cache: List[Tuple[str, Dict]] = []


def _build_bm25_index(docs_data: List[Tuple[str, Dict]]):
    """Build BM25Okapi index from document corpus."""
    global _bm25_index, _bm25_corpus
    try:
        from rank_bm25 import BM25Okapi
        _bm25_corpus = [content.lower().split() for content, _ in docs_data]
        _bm25_index = BM25Okapi(_bm25_corpus)
        logger.info(f"BM25 index built ({len(_bm25_corpus)} docs).")
    except ImportError:
        logger.warning("rank_bm25 not installed — BM25 hybrid search disabled. Run: pip install rank-bm25")
    except Exception as e:
        logger.warning(f"BM25 index build failed: {e}")


def _build_faiss_store():
    """Build FAISS vector store — uses local HuggingFace embeddings (no API key needed),
    falls back to Gemini embeddings if GEMINI_API_KEY is set."""
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document

    docs_data = get_all_documents()
    _build_bm25_index(docs_data)
    documents = [
        Document(page_content=content, metadata=meta)
        for content, meta in docs_data
    ]

    # Try local HuggingFace embeddings first (free, no API key, ~90MB model)
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        store = FAISS.from_documents(documents, embeddings)
        logger.info(f"FAISS built with local HuggingFace embeddings ({len(documents)} docs).")
        return store
    except Exception as e:
        logger.warning(f"HuggingFace embeddings failed ({e}), trying Gemini...")

    # Fallback: Gemini embeddings
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=gemini_key,
            request_timeout=15,
        )
        store = FAISS.from_documents(documents, embeddings)
        logger.info(f"FAISS built with Gemini embeddings ({len(documents)} docs).")
        return store

    raise RuntimeError("No embeddings provider available")


def _build_tfidf_fallback():
    """Build TF-IDF fallback for when FAISS is unavailable."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    docs_data = get_all_documents()
    _build_bm25_index(docs_data)
    texts = [content for content, _ in docs_data]
    metas = [meta for _, meta in docs_data]

    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(texts)

    logger.info(f"TF-IDF fallback built with {len(texts)} documents.")
    return {"vectorizer": vectorizer, "matrix": matrix, "texts": texts, "metas": metas}


def get_knowledge_base():
    """Return the initialized knowledge base (lazy singleton)."""
    global _vector_store, _tfidf_fallback, _docs_cache

    if _vector_store is not None or _tfidf_fallback is not None:
        return

    _docs_cache = get_all_documents()

    # Always try FAISS first (uses local HuggingFace embeddings — no API key needed)
    try:
        _vector_store = _build_faiss_store()
        logger.info("FAISS vector store ready.")
        return
    except Exception as e:
        logger.warning(f"FAISS build failed ({e}). Falling back to TF-IDF.")

    _tfidf_fallback = _build_tfidf_fallback()
    logger.info("Using TF-IDF fallback for knowledge retrieval.")


def _rrf_fuse(ranked_lists: List[List[str]], k: int = 60) -> List[Tuple[str, float]]:
    """
    Reciprocal Rank Fusion: merges multiple ranked lists into one.
    Returns [(doc_id, rrf_score)] sorted descending.
    k=60 is the standard constant that dampens high-rank advantage.
    """
    scores: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _bm25_ranked_ids(query: str, n: int) -> List[str]:
    """Return doc indices (as strings) ranked by BM25 score for query."""
    if _bm25_index is None:
        return []
    tokens = query.lower().split()
    bm25_scores = _bm25_index.get_scores(tokens)
    ranked_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
    return [str(i) for i in ranked_idx[:n]]


def retrieve(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve top-k relevant documents using FAISS semantic search + BM25
    fused with Reciprocal Rank Fusion (RRF).  Falls back to TF-IDF alone
    when FAISS is unavailable.
    """
    get_knowledge_base()  # ensure initialized

    # ── FAISS path (primary) ─────────────────────────────────────────────────
    if _vector_store is not None:
        try:
            fetch_n = max(k * 3, 10)  # fetch extra candidates for RRF re-ranking
            hits = _vector_store.similarity_search_with_relevance_scores(query, k=fetch_n)

            # FAISS ranking: index in hits list
            faiss_ids   = [str(i) for i in range(len(hits))]
            bm25_ids    = _bm25_ranked_ids(query, fetch_n)

            if bm25_ids:
                # Map BM25 doc-cache indices to FAISS candidate indices
                # Both are over the same _docs_cache ordering so indices align
                fused = _rrf_fuse([faiss_ids, bm25_ids])
                top_indices = [int(doc_id) for doc_id, _ in fused[:k] if int(doc_id) < len(hits)]
            else:
                top_indices = list(range(min(k, len(hits))))

            results = []
            for idx in top_indices:
                doc, faiss_score = hits[idx]
                results.append({
                    "content":  doc.page_content[:800],
                    "title":    doc.metadata.get("title", "Unknown"),
                    "id":       doc.metadata.get("id", ""),
                    "category": doc.metadata.get("category", ""),
                    "score":    round(faiss_score, 3),
                    "retrieval": "hybrid" if bm25_ids else "semantic",
                })
            return results
        except Exception as e:
            logger.warning(f"FAISS retrieval failed ({e}). Using TF-IDF.")

    # ── TF-IDF fallback ──────────────────────────────────────────────────────
    if _tfidf_fallback is not None:
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        vect   = _tfidf_fallback["vectorizer"]
        matrix = _tfidf_fallback["matrix"]
        texts  = _tfidf_fallback["texts"]
        metas  = _tfidf_fallback["metas"]

        query_vec  = vect.transform([query])
        tfidf_scores = cosine_similarity(query_vec, matrix).flatten()
        tfidf_ids  = [str(i) for i in tfidf_scores.argsort()[::-1][:k * 3]]
        bm25_ids   = _bm25_ranked_ids(query, k * 3)

        if bm25_ids:
            fused     = _rrf_fuse([tfidf_ids, bm25_ids])
            top_idxs  = [int(did) for did, _ in fused[:k]]
        else:
            top_idxs  = [int(i) for i in tfidf_ids[:k]]

        results = []
        for idx in top_idxs:
            if idx < len(texts) and tfidf_scores[idx] > 0.01:
                results.append({
                    "content":   texts[idx][:800],
                    "title":     metas[idx].get("title", "Unknown"),
                    "id":        metas[idx].get("id", ""),
                    "category":  metas[idx].get("category", ""),
                    "score":     round(float(tfidf_scores[idx]), 3),
                    "retrieval": "hybrid-tfidf" if bm25_ids else "tfidf",
                })
        return results

    return []


def retrieve_for_fault(fault_type: str, equipment_type: str = "pump", k: int = 3) -> List[Dict[str, Any]]:
    """Targeted retrieval combining fault type + equipment context."""
    query = f"{fault_type} {equipment_type} maintenance procedure corrective action root cause"
    return retrieve(query, k=k)


def add_document(doc_id: str, title: str, content: str, category: str = "engineer_feedback") -> bool:
    """Add a new document to the live knowledge base (FAISS + BM25 + TF-IDF)."""
    global _vector_store, _tfidf_fallback, _docs_cache, _bm25_index, _bm25_corpus

    get_knowledge_base()  # ensure initialized

    meta = {"id": doc_id, "title": title, "category": category}
    _docs_cache.append((content, meta))

    # Rebuild BM25 index with new document (fast for ~50 docs)
    if _bm25_index is not None:
        try:
            from rank_bm25 import BM25Okapi
            _bm25_corpus.append(content.lower().split())
            _bm25_index = BM25Okapi(_bm25_corpus)
        except Exception as e:
            logger.warning(f"BM25 update failed: {e}")

    if _vector_store is not None:
        try:
            from langchain_core.documents import Document
            _vector_store.add_documents([Document(page_content=content, metadata=meta)])
            logger.info(f"Added '{doc_id}' to FAISS store ({len(_docs_cache)} total docs).")
            return True
        except Exception as e:
            logger.warning(f"FAISS add_document failed: {e}")

    if _tfidf_fallback is not None:
        try:
            from scipy.sparse import vstack
            new_vec = _tfidf_fallback["vectorizer"].transform([content])
            _tfidf_fallback["matrix"] = vstack([_tfidf_fallback["matrix"], new_vec])
            _tfidf_fallback["texts"].append(content)
            _tfidf_fallback["metas"].append(meta)
            logger.info(f"Added '{doc_id}' to TF-IDF store.")
            return True
        except Exception as e:
            logger.warning(f"TF-IDF add_document failed: {e}")

    return False


def knowledge_base_stats() -> dict:
    """Return document count and backend type — shown in UI for judge demo."""
    get_knowledge_base()
    if _vector_store is not None:
        backend = "FAISS+BM25 Hybrid (RRF)" if _bm25_index is not None else "FAISS (HuggingFace)"
    elif _tfidf_fallback is not None:
        backend = "TF-IDF+BM25 Hybrid (RRF)" if _bm25_index is not None else "TF-IDF"
    else:
        backend = "uninitialized"
    return {
        "total_documents": len(_docs_cache),
        "backend": backend,
        "bm25_enabled": _bm25_index is not None,
    }
