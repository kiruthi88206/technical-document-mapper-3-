import os
import numpy as np
from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_model = None
_model_attempted = False

def get_embedding_model():
    """Attempt to load sentence-transformers model only when explicitly enabled."""
    global _model, _model_attempted
    if not _model_attempted:
        _model_attempted = True
        if os.getenv("ENABLE_SENTENCE_TRANSFORMERS", "0") == "1":
            try:
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                _model = None
    return _model

class SemanticSimilarity:
    """Computes semantic similarity between technical concepts and sentences."""

    @classmethod
    def compute_similarity_matrix(cls, terms: List[str]) -> Optional[np.ndarray]:
        """
        Compute vector similarity matrix between concept terms using:
        1. Sentence transformers (if ENABLE_SENTENCE_TRANSFORMERS=1)
        2. Fast subword / character-ngram TF-IDF vector cosine similarity (deterministic, sub-millisecond)
        """
        if not terms or len(terms) < 2:
            return None

        # 1. Check if sentence transformers is enabled
        model = get_embedding_model()
        if model is not None:
            try:
                embeddings = model.encode(terms, convert_to_numpy=True, show_progress_bar=False)
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1e-10
                norm_embeddings = embeddings / norms
                sim_matrix = np.dot(norm_embeddings, norm_embeddings.T)
                return sim_matrix
            except Exception:
                pass

        # 2. Resilient and lightning-fast TF-IDF subword vector similarity
        try:
            vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
            tfidf_mat = vectorizer.fit_transform(terms)
            sim_mat = cosine_similarity(tfidf_mat, tfidf_mat)
            return sim_mat
        except Exception:
            return None

    @classmethod
    def token_overlap_similarity(cls, term_a: str, term_b: str) -> float:
        """Fallback character/word Jaccard similarity when embeddings are unavailable."""
        words_a = set(term_a.lower().split())
        words_b = set(term_b.lower().split())
        union = words_a.union(words_b)
        if not union:
            return 0.0
        return len(words_a.intersection(words_b)) / len(union)
