import re
import numpy as np
from config import Config

# Sentence Transformers lazy loading support
ST_AVAILABLE = True
st_model = None

def get_st_model():
    global st_model, ST_AVAILABLE
    if st_model is None and ST_AVAILABLE:
        try:
            from sentence_transformers import SentenceTransformer
            print("[SentenceTransformers] Loading all-MiniLM-L6-v2 embedding model...")
            st_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[SentenceTransformers] Model loaded successfully.")
        except Exception as e:
            print(f"[SentenceTransformers] Info: Using scikit-learn TF-IDF semantic embeddings ({e})")
            ST_AVAILABLE = False
            st_model = None
    return st_model


# Fallback TF-IDF cosine similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RelationshipMapper:
    def __init__(self, threshold=None):
        self.threshold = threshold if threshold is not None else Config.SIMILARITY_THRESHOLD

    def discover_relationships(self, concepts, sentences, full_text):
        """Discover semantic, co-occurrence, and contextual relationships between concepts."""
        if not concepts or len(concepts) < 2:
            return []

        concept_names = [c['name'] for c in concepts]
        concept_dict = {c['name']: c for c in concepts}
        
        # 1. Calculate Embeddings and Cosine Similarity
        similarity_matrix = self._compute_semantic_matrix(concept_names, sentences)
        
        relationships = []
        n = len(concept_names)
        
        for i in range(n):
            for j in range(i + 1, n):
                name1 = concept_names[i]
                name2 = concept_names[j]
                
                # Semantic similarity score
                sem_score = float(similarity_matrix[i][j])
                
                # Co-occurrence analysis across sentences
                co_occur_count, sample_sentence = self._analyze_co_occurrence(name1, name2, sentences)
                
                # Calculate combined relationship strength
                co_occur_boost = min(0.35, co_occur_count * 0.12)
                strength = round(min(0.98, max(sem_score, 0.0) * 0.7 + co_occur_boost), 2)
                
                if strength >= self.threshold or co_occur_count > 0:
                    rel_type = "semantic_similarity"
                    reason = f"High semantic similarity score of {strength:.2f}."
                    
                    if co_occur_count > 0:
                        rel_type = "co_occurrence"
                        reason = f"Co-occurs {co_occur_count} time(s) in document context: '{sample_sentence[:120]}...'"
                    elif sem_score > 0.65:
                        reason = f"Strong conceptual and vector alignment ({sem_score:.2f})."

                    relationships.append({
                        'source': name1,
                        'target': name2,
                        'relationship_type': rel_type,
                        'strength': strength,
                        'semantic_score': round(max(0.0, sem_score), 2),
                        'co_occurrence_count': co_occur_count,
                        'reason': reason
                    })

        # Sort by strength desc
        relationships.sort(key=lambda x: x['strength'], reverse=True)
        return relationships

    def _compute_semantic_matrix(self, terms, sentences):
        model = get_st_model()
        if model:
            try:
                # Generate embeddings for terms + context definitions
                embeddings = model.encode(terms, convert_to_numpy=True)
                sim = cosine_similarity(embeddings)
                return sim
            except Exception as e:
                print(f"[RelationshipMapper] SentenceTransformer error: {e}")


        # Scikit-learn TF-IDF fallback vectorizer
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2))
            # Fit on sentences text + term list
            corpus = sentences + terms
            vectorizer.fit(corpus)
            term_vectors = vectorizer.transform(terms)
            sim = cosine_similarity(term_vectors)
            return sim
        except Exception as e:
            print(f"[RelationshipMapper] TF-IDF fallback error: {e}")
            # Dummy similarity fallback based on word overlap
            n = len(terms)
            sim = np.zeros((n, n))
            for i in range(n):
                for j in range(n):
                    if i == j:
                        sim[i][j] = 1.0
                    else:
                        w1 = set(terms[i].lower().split())
                        w2 = set(terms[j].lower().split())
                        overlap = len(w1.intersection(w2))
                        sim[i][j] = overlap / max(len(w1.union(w2)), 1)
            return sim

    def _analyze_co_occurrence(self, term1, term2, sentences):
        p1 = re.compile(rf'\b{re.escape(term1)}\b', re.IGNORECASE)
        p2 = re.compile(rf'\b{re.escape(term2)}\b', re.IGNORECASE)
        
        count = 0
        sample_sentence = ""
        for s in sentences:
            if p1.search(s) and p2.search(s):
                count += 1
                if not sample_sentence:
                    sample_sentence = s.strip()
        
        return count, sample_sentence
