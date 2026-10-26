"""
NLP Processing and Terminology Extraction Service.
Combines spaCy, NLTK, TF-IDF, and linguistic heuristics to extract domain terminology,
rank technical concepts, and construct contextual glossaries.
"""
import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from config import Config

# Optional spaCy loading
SPACY_NLP = None
try:
    import spacy
    try:
        SPACY_NLP = spacy.load("en_core_web_sm")
    except Exception:
        SPACY_NLP = None
except ImportError:
    SPACY_NLP = None

# Optional NLTK loading with safe fallback
NLTK_AVAILABLE = False
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    try:
        nltk.data.find('corpora/stopwords')
        NLTK_STOPWORDS = set(stopwords.words('english'))
        NLTK_AVAILABLE = True
    except Exception:
        # Fallback built-in stop words
        NLTK_STOPWORDS = set()
except ImportError:
    NLTK_STOPWORDS = set()

# Built-in comprehensive stop words to ensure zero failure if NLTK data is missing
BUILTIN_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", 
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", 
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", 
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", 
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", 
    "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", 
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", 
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", 
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", 
    "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", 
    "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", 
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", 
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", 
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", 
    "your", "yours", "yourself", "yourselves", "also", "thus", "therefore", "however", "furthermore",
    "moreover", "respectively", "etc", "e.g", "i.e", "et", "al", "fig", "figure", "table", "section",
    "chapter", "page", "result", "results", "using", "used", "uses", "use", "approach", "paper", "study",
    "present", "presents", "presented", "shown", "shows", "based", "first", "second", "third", "one", "two"
}

ALL_STOPWORDS = BUILTIN_STOPWORDS.union(NLTK_STOPWORDS)

# Technical Categories and Indicator Keywords
CATEGORY_PATTERNS = {
    "Models & Algorithms": [
        "model", "algorithm", "network", "transformer", "bert", "lstm", "cnn", "rnn", "classifier",
        "regression", "encoder", "decoder", "clustering", "heuristic", "optimization", "agent", "perceptron"
    ],
    "Data & Representations": [
        "data", "dataset", "embedding", "vector", "feature", "matrix", "tensor", "corpus", "token",
        "vocabulary", "graph", "knowledge graph", "index", "database", "schema", "record", "storage"
    ],
    "Architectures & Infrastructure": [
        "architecture", "pipeline", "framework", "system", "infrastructure", "cluster", "server",
        "service", "microservice", "api", "cloud", "docker", "kubernetes", "distributed", "node"
    ],
    "Techniques & Methods": [
        "processing", "extraction", "analysis", "similarity", "tokenization", "lemmatization",
        "tf-idf", "attention", "backpropagation", "pre-training", "fine-tuning", "validation", "evaluation", "metric"
    ]
}


class NLPProcessor:
    """Core NLP Engine for Document Terminology and Concept Analysis."""

    def __init__(self):
        self.spacy_enabled = SPACY_NLP is not None
        print(f"[NLP ENGINE] Initialized. spaCy active: {self.spacy_enabled}")

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences cleanly."""
        if not text:
            return []
        if self.spacy_enabled:
            doc = SPACY_NLP(text[:100000])  # limit for speed on massive docs
            return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 5]
        
        # Regex sentence splitter fallback
        raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])', text)
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 5]
        return sentences

    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into lowercase alphanumeric words."""
        return [w.lower() for w in re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-_]*\b', text)]

    def extract_candidate_terms(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """
        Extract technical candidate terms:
        1. Multi-word technical noun phrases (e.g. 'Convolutional Neural Network', 'TF-IDF')
        2. Technical acronyms and abbreviations (e.g. 'NLP', 'BERT', 'REST')
        3. Domain entities (from spaCy if active, or pattern matchers)
        """
        candidates = []
        
        # 1. spaCy noun chunks & named entities if available
        if self.spacy_enabled:
            doc = SPACY_NLP(text[:150000])
            for chunk in doc.noun_chunks:
                clean_chunk = chunk.text.strip()
                # Strip leading determiners/articles (the, a, an, this, these)
                clean_chunk = re.sub(r'^(the|a|an|this|that|these|those)\s+', '', clean_chunk, flags=re.IGNORECASE).strip()
                if 2 <= len(clean_chunk.split()) <= 4 and len(clean_chunk) > 3:
                    if not any(w.lower() in ALL_STOPWORDS for w in clean_chunk.split()):
                        candidates.append(clean_chunk)
            
            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART", "LAW", "NORP"):
                    if len(ent.text.strip()) > 2 and ent.text.lower() not in ALL_STOPWORDS:
                        candidates.append(ent.text.strip())

        # 2. Heuristic Pattern Extractor: Acronyms, Capitalized Technical Terms & Multi-word NPs
        # Match Acronyms: NLP, TF-IDF, BERT, API, REST, RNN, CNN, etc.
        acronyms = re.findall(r'\b[A-Z][A-Z0-9\-_]{1,6}[A-Z0-9]\b', text)
        for acr in acronyms:
            if acr.lower() not in ALL_STOPWORDS and len(acr) >= 2:
                candidates.append(acr)

        # Match Capitalized Multi-Word Concepts: "Knowledge Graph", "Natural Language Processing", "Vector Embedding"
        cap_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b', text)
        for phrase in cap_phrases:
            words = phrase.split()
            if not all(w.lower() in ALL_STOPWORDS for w in words):
                candidates.append(phrase)

        # Match Technical Compound Phrases: "term extraction", "sentence co-occurrence", "semantic similarity"
        compound_pattern = re.findall(r'\b[a-zA-Z]{3,}(?:-[a-zA-Z]{3,})+\b', text)
        for comp in compound_pattern:
            if comp.lower() not in ALL_STOPWORDS:
                candidates.append(comp)

        # 3. Fallback N-Gram extraction for technical compound terms
        TECHNICAL_KEYWORDS = {
            "network", "model", "embedding", "vector", "graph", "transformer", "attention",
            "similarity", "architecture", "mechanism", "service", "gateway", "cluster",
            "cache", "queue", "pipeline", "processing", "learning", "representation", "database",
            "tokenization", "lemmatization", "dependency", "extraction", "intelligence"
        }
        COMMON_VERBS = {
            "divides", "employ", "employs", "uses", "enables", "produces", "creates", "shows",
            "shown", "provides", "transforms", "measured", "measures", "consists", "relies",
            "depends", "represents", "identifies", "processes", "modern", "individual", "various",
            "different", "similar", "strong", "large", "new", "first", "second"
        }
        
        # Clean text tokens
        tokens = [w for w in re.findall(r'\b[a-zA-Z0-9\-_]{3,}\b', text) if w.lower() not in ALL_STOPWORDS and w.lower() not in COMMON_VERBS]
        for i in range(len(tokens) - 1):
            w1, w2 = tokens[i].lower(), tokens[i+1].lower()
            if w1 not in ALL_STOPWORDS and w2 not in ALL_STOPWORDS and w1 not in COMMON_VERBS and w2 not in COMMON_VERBS:
                if not (w1.isdigit() or w2.isdigit()):
                    # Only accept bigram if it contains a known technical keyword or standard technical morphology
                    if any(kw in w1 or kw in w2 for kw in TECHNICAL_KEYWORDS):
                        candidates.append(f"{tokens[i]} {tokens[i+1]}")

        # Normalization and canonical form aggregation
        canonical_map = defaultdict(list)
        for term in candidates:
            norm_key = re.sub(r'[\s\-_]+', ' ', term.strip().lower())
            if len(norm_key) >= 3 and norm_key not in ALL_STOPWORDS:
                canonical_map[norm_key].append(term.strip())

        # Select most common surface form (preferring capitalized/acronym forms)
        normalized_terms = []
        for norm_key, surface_forms in canonical_map.items():
            freq = len(surface_forms)
            # Pick best surface representation (e.g., 'TF-IDF' over 'tf-idf')
            best_surface = Counter(surface_forms).most_common(1)[0][0]
            # Check if any form is uppercase or title case
            title_forms = [f for f in surface_forms if f.isupper() or f.istitle()]
            if title_forms:
                best_surface = Counter(title_forms).most_common(1)[0][0]

            normalized_terms.append({
                "term": best_surface,
                "norm_key": norm_key,
                "raw_frequency": freq
            })

        return normalized_terms

    def compute_tfidf_rankings(self, sentences: List[str], candidate_terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank technical terms using TF-IDF across document sentence contexts.
        Sentences serve as sub-documents to reward terms that are specifically clustered and salient.
        """
        if not sentences or not candidate_terms:
            return []

        # Build vocabulary from candidates
        term_lookup = {item["norm_key"]: item for item in candidate_terms}
        vocabulary = list(term_lookup.keys())

        try:
            vectorizer = TfidfVectorizer(
                vocabulary=vocabulary,
                ngram_range=(1, 3),
                lowercase=True,
                stop_words='english'
            )
            tfidf_matrix = vectorizer.fit_transform(sentences)
            
            # Sum tf-idf scores across all sentences
            mean_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
            max_tfidf = np.asarray(tfidf_matrix.max(axis=0).toarray()).flatten()

            ranked = []
            for idx, key in enumerate(vocabulary):
                raw_item = term_lookup[key]
                score = float((mean_tfidf[idx] * 0.4) + (max_tfidf[idx] * 0.6))
                
                # Boost acronyms and multi-words slightly
                boost = 1.0
                if raw_item["term"].isupper() and len(raw_item["term"]) <= 6:
                    boost = 1.25  # Acronym bonus
                elif len(raw_item["term"].split()) >= 2:
                    boost = 1.15  # Multi-word concept bonus

                final_score = round(score * boost * 100, 3)
                
                ranked.append({
                    "term": raw_item["term"],
                    "norm_key": key,
                    "frequency": raw_item["raw_frequency"],
                    "tfidf_score": final_score
                })

            ranked.sort(key=lambda x: (x["tfidf_score"], x["frequency"]), reverse=True)
            return ranked
        except Exception as e:
            print(f"[NLP WARNING] TF-IDF computation fell back to frequency ranking ({e})")
            # Fallback to pure frequency ranking
            fallback_ranked = []
            for item in candidate_terms:
                fallback_ranked.append({
                    "term": item["term"],
                    "norm_key": item["norm_key"],
                    "frequency": item["raw_frequency"],
                    "tfidf_score": round(item["raw_frequency"] * 1.5, 2)
                })
            fallback_ranked.sort(key=lambda x: x["frequency"], reverse=True)
            return fallback_ranked

    def categorize_concept(self, term: str) -> str:
        """Assign category for visual styling and domain classification."""
        term_lower = term.lower()
        for category, keywords in CATEGORY_PATTERNS.items():
            for kw in keywords:
                if kw in term_lower:
                    return category
        
        # Heuristic rules
        if term.isupper() and len(term) <= 6:
            return "Frameworks & Tools"
        if len(term.split()) >= 3:
            return "Architectures & Infrastructure"
        return "Core Concepts"

    def extract_definition_and_context(self, term: str, norm_key: str, sentences: List[str]) -> Dict[str, Any]:
        """
        Locate definition sentences or prime contextual occurrences for a term.
        Distinguishes verbatim source definitions from contextual snippets.
        """
        matching_sentences = []
        term_pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)

        # Common linguistic definition patterns
        definition_cues = [
            re.compile(r'\b' + re.escape(term) + r'\s+(?:is|are|refers to|is defined as|represents|signifies|acts as|serves as)\b', re.IGNORECASE),
            re.compile(r'\b(?:known as|termed|called)\s+' + re.escape(term) + r'\b', re.IGNORECASE),
            re.compile(r'\b' + re.escape(term) + r'\s*,\s*(?:which|that)\s+(?:is|are|enables|provides)\b', re.IGNORECASE)
        ]

        best_definition = None
        is_explicit_definition = False

        for sentence in sentences:
            if term_pattern.search(sentence):
                clean_sent = sentence.strip()
                matching_sentences.append(clean_sent)
                
                # Check for explicit definition cue
                for cue in definition_cues:
                    if cue.search(sentence):
                        best_definition = clean_sent
                        is_explicit_definition = True
                        break
                if is_explicit_definition:
                    break

        if not matching_sentences:
            return {
                "definition": f"Key technical concept mentioned in the document: '{term}'.",
                "origin": "Synthesized Reference",
                "is_explicit_definition": False,
                "context_sentence": "Term identified during lexical scanning.",
                "occurrences": 0
            }

        # If no explicit definition cue found, select the most informative sentence (length 40-200 chars)
        if not best_definition:
            candidate_sents = [s for s in matching_sentences if 30 <= len(s) <= 280]
            if candidate_sents:
                best_definition = candidate_sents[0]
            else:
                best_definition = matching_sentences[0]

        return {
            "definition": best_definition,
            "origin": "Document Source Text" if is_explicit_definition else "Contextual Excerpt",
            "is_explicit_definition": is_explicit_definition,
            "context_sentence": matching_sentences[0] if matching_sentences else best_definition,
            "occurrences": len(matching_sentences)
        }

    def process_document(self, text: str, max_concepts: int = 30) -> Dict[str, Any]:
        """
        End-to-end NLP pipeline:
        1. Sentence splitting
        2. Candidate technical term extraction
        3. TF-IDF scoring and ranking
        4. Concept categorization
        5. Glossary generation
        """
        sentences = self.split_sentences(text)
        if not sentences:
            raise ValueError("Document contains no valid sentences.")

        candidates = self.extract_candidate_terms(text, sentences)
        if not candidates:
            # Fallback extraction from frequent words
            words = [w for w in self.tokenize_words(text) if len(w) > 4 and w not in ALL_STOPWORDS]
            word_counts = Counter(words).most_common(max_concepts)
            candidates = [{"term": w.title(), "norm_key": w, "raw_frequency": count} for w, count in word_counts]

        ranked_terms = self.compute_tfidf_rankings(sentences, candidates)
        top_concepts = ranked_terms[:max_concepts]

        # Generate full concept items and glossary entries
        concepts_list = []
        glossary_list = []

        for rank, item in enumerate(top_concepts, start=1):
            category = self.categorize_concept(item["term"])
            context_data = self.extract_definition_and_context(item["term"], item["norm_key"], sentences)

            concept_record = {
                "concept_id": f"c_{rank}",
                "name": item["term"],
                "norm_key": item["norm_key"],
                "rank": rank,
                "category": category,
                "frequency": item["frequency"],
                "tfidf_score": item["tfidf_score"],
                "definition": context_data["definition"],
                "origin": context_data["origin"],
                "is_explicit_definition": context_data["is_explicit_definition"],
                "context_sentence": context_data["context_sentence"]
            }
            concepts_list.append(concept_record)

            glossary_list.append({
                "term": item["term"],
                "category": category,
                "frequency": item["frequency"],
                "definition": context_data["definition"],
                "origin": context_data["origin"],
                "context_sentence": context_data["context_sentence"]
            })

        return {
            "sentence_count": len(sentences),
            "sentences": sentences,
            "concepts": concepts_list,
            "glossary": glossary_list
        }


# Singleton NLP Processor
nlp_processor = NLPProcessor()
