import re
from typing import List, Dict, Any

CATEGORY_RULES = {
    "Technology & Framework": [
        r'\b(react|react\.js|vue|angular|fastapi|flask|django|neo4j|docker|kubernetes|python|javascript|typescript|nodejs|node\.js|d3|d3\.js|vis\.js|vis-network|tailwind|git|github|mongodb|postgresql|redis|kafka|graphql|pytorch|tensorflow|spacy|nltk|scikit-learn|huggingface|transformers|bert|gpt|llama)\b'
    ],
    "Algorithm & Method": [
        r'\b(tf-idf|tfidf|cosine similarity|semantic similarity|tokenization|lemmatization|stemming|pos tagging|ner|named entity recognition|embedding|word2vec|fasttext|clustering|k-means|gradient descent|backpropagation|attention mechanism|pagerank|breadth-first|depth-first|classification|regression|parsing|dependency parsing|vectorization)\b'
    ],
    "Architecture & Pattern": [
        r'\b(knowledge graph|graph database|relational database|microservices|rest api|restful|pipeline|etl|client-server|mvc|monolith|message queue|data lake|data warehouse|semantic web|ontology|triplestore|graph structure|directed graph|undirected graph)\b'
    ],
    "Data & Metric": [
        r'\b(dataset|corpus|feature vector|embedding matrix|loss function|accuracy|precision|recall|f1-score|f1 score|bleu|perplexity|auc|roc|latency|throughput|edge weight|co-occurrence|node degree|centrality|eigenvector)\b'
    ],
    "Domain Concept": [
        r'\b(natural language processing|nlp|machine learning|deep learning|artificial intelligence|information retrieval|graph theory|computer vision|semantic analysis|sentiment analysis|text mining|data science|concept mapping|terminology extraction|knowledge representation)\b'
    ]
}

class ConceptCategorizer:
    """Categorizes technical terms into distinct semantic domains with distinct color mappings."""

    CATEGORY_COLORS = {
        "Technology & Framework": "#3b82f6",     # Blue
        "Algorithm & Method": "#10b981",         # Emerald / Green
        "Architecture & Pattern": "#8b5cf6",     # Purple / Violet
        "Data & Metric": "#f59e0b",              # Amber / Orange
        "Domain Concept": "#06b6d4",             # Cyan
        "General Technical": "#64748b"           # Slate
    }

    @classmethod
    def categorize(cls, term: str) -> str:
        term_lower = term.lower().strip()
        for cat, patterns in CATEGORY_RULES.items():
            for pat in patterns:
                if re.search(pat, term_lower, re.IGNORECASE):
                    return cat

        # Heuristic rules
        if any(w in term_lower for w in ["graph", "network", "system", "engine", "service", "base"]):
            return "Architecture & Pattern"
        if any(w in term_lower for w in ["algorithm", "model", "method", "analysis", "detection", "mining", "learning"]):
            return "Algorithm & Method"
        if any(w in term_lower for w in ["data", "vector", "score", "index", "rate", "weight", "frequency"]):
            return "Data & Metric"
        if any(w in term_lower for w in ["tool", "library", "framework", "software", "api", "database"]):
            return "Technology & Framework"

        return "Domain Concept"

    @classmethod
    def get_color(cls, category: str) -> str:
        return cls.CATEGORY_COLORS.get(category, cls.CATEGORY_COLORS["General Technical"])
