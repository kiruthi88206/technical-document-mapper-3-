import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from .preprocessor import Preprocessor, COMMON_STOPWORDS
from .categorizer import ConceptCategorizer

class TermExtractor:
    """Extracts, ranks, and categorizes technical terms from document text."""

    @classmethod
    def extract_candidate_noun_phrases(cls, text: str, sentences: List[str]) -> List[str]:
        """Extract multi-word and technical noun phrase candidates using spaCy or POS regex patterns."""
        candidates = []
        nlp = Preprocessor.get_spacy_nlp()

        if nlp is not None and hasattr(nlp, "pipe"):
            try:
                # Use spaCy noun chunks & entities if available
                doc = nlp(text[:250000])
                for chunk in doc.noun_chunks:
                    clean_chunk = chunk.text.strip()
                    # Filter stop words at edges
                    words = clean_chunk.split()
                    while words and words[0].lower() in COMMON_STOPWORDS:
                        words.pop(0)
                    while words and words[-1].lower() in COMMON_STOPWORDS:
                        words.pop()
                    if words and 1 <= len(words) <= 4:
                        phrase = " ".join(words)
                        if len(phrase) > 2 and not phrase.isnumeric():
                            candidates.append(phrase)

                # Also grab entities
                for ent in doc.ents:
                    if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "EVENT", "LAW", "NORP"]:
                        clean_ent = ent.text.strip()
                        if len(clean_ent) > 2 and clean_ent.lower() not in COMMON_STOPWORDS:
                            candidates.append(clean_ent)
            except Exception:
                pass

        # Regex-based technical pattern extraction (Capitalized Tech Terms, Acronyms, Hyphenated terms)
        tech_pattern = re.compile(
            r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}|[A-Z]{2,}(?:-[A-Za-z0-9]+)?|[a-z]+(?:-[a-z]+)+)\b'
        )
        for sent in sentences:
            matches = tech_pattern.findall(sent)
            for m in matches:
                clean_m = m.strip()
                if clean_m.lower() not in COMMON_STOPWORDS and len(clean_m) > 2:
                    candidates.append(clean_m)

        # Common multi-word computer science & engineering phrases
        n_gram_pattern = re.compile(r'\b[a-zA-Z][a-zA-Z0-9_-]*(?:\s+[a-zA-Z][a-zA-Z0-9_-]*){1,2}\b')
        for sent in sentences:
            for phrase in n_gram_pattern.findall(sent):
                p_lower = phrase.lower()
                words = p_lower.split()
                if not any(w in COMMON_STOPWORDS for w in words):
                    candidates.append(phrase)

        return candidates

    @classmethod
    def extract_and_rank_terms(
        cls, 
        text: str, 
        sentences: List[str], 
        top_k: int = 35, 
        min_freq: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Extract key terms, rank using TF-IDF and term frequency,
        and attach context sentences, category, and score.
        """
        if not text or not sentences:
            return []

        # 1. Candidate gathering
        raw_candidates = cls.extract_candidate_noun_phrases(text, sentences)
        
        # Also extract significant single tokens
        single_tokens = []
        for s in sentences:
            single_tokens.extend(Preprocessor.tokenize(s))
        
        # Canonicalize candidates (normalize casing while preserving display capitalization)
        case_map = {}
        counts = Counter()
        
        for cand in raw_candidates:
            clean = cand.strip()
            # Normalize casing key
            key = clean.lower()
            if key in COMMON_STOPWORDS or len(key) < 3 or key.isnumeric():
                continue
            counts[key] += 1
            # Keep best representative casing
            if key not in case_map or (clean[0].isupper() and not case_map[key][0].isupper()):
                case_map[key] = clean

        for tok in single_tokens:
            if len(tok) > 2 and tok not in COMMON_STOPWORDS:
                counts[tok] += 1
                if tok not in case_map:
                    case_map[tok] = tok.title()

        # 2. Compute TF-IDF over document sentences as pseudo-documents
        tfidf_scores = defaultdict(float)
        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                stop_words='english',
                max_features=500
            )
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            avg_tfidf = tfidf_matrix.mean(axis=0).A1
            for feat, score in zip(feature_names, avg_tfidf):
                tfidf_scores[feat.lower()] = float(score)
        except Exception:
            # Fallback simple TF calculation
            total_words = max(1, sum(counts.values()))
            for k, c in counts.items():
                tfidf_scores[k] = c / total_words

        # 3. Score and combine
        ranked_items = []
        for key, freq in counts.items():
            if freq < min_freq:
                continue
            
            # Lookup or compute TF-IDF score
            score = tfidf_scores.get(key, 0.0)
            if score == 0.0:
                # Calculate based on sub-terms or frequency
                score = (freq / len(sentences)) * (math.log(1 + len(sentences)))
            
            # Boost multi-word terms and capitalized technical acronyms
            display_name = case_map.get(key, key.title())
            multiplier = 1.0
            if " " in display_name:
                multiplier *= 1.35
            if display_name.isupper() and len(display_name) <= 6:
                multiplier *= 1.40
            
            composite_score = score * multiplier * (math.log(1 + freq))
            
            ranked_items.append({
                "term_key": key,
                "label": display_name,
                "frequency": freq,
                "tfidf_score": round(score, 4),
                "composite_score": round(composite_score, 4)
            })

        # Sort by composite score descending
        ranked_items.sort(key=lambda x: (x["composite_score"], x["frequency"]), reverse=True)
        top_candidates = ranked_items[:top_k]

        # 4. Filter near-duplicates (e.g. if 'Knowledge Graph' is present, don't duplicate 'The Knowledge Graph')
        final_terms = []
        seen_keys = set()
        
        for item in top_candidates:
            k = item["term_key"]
            # Check if an existing term is a substring or identical
            is_sub = False
            for seen in list(seen_keys):
                if k == seen or (len(k) > 4 and len(seen) > 4 and (k in seen or seen in k) and abs(len(k) - len(seen)) <= 2):
                    is_sub = True
                    break
            if not is_sub:
                seen_keys.add(k)
                final_terms.append(item)

        # 5. Attach contextual sentences (glossary definition snippet & occurrences)
        enriched_terms = []
        for i, item in enumerate(final_terms, 1):
            lbl = item["label"]
            term_key = item["term_key"]
            category = ConceptCategorizer.categorize(lbl)
            
            # Find context sentences
            contexts = []
            escaped_term = re.escape(lbl)
            pattern = re.compile(rf'\b{escaped_term}\b', re.IGNORECASE)
            
            for sent in sentences:
                if pattern.search(sent):
                    contexts.append(sent.strip())
                    if len(contexts) >= 3:
                        break

            definition = contexts[0] if contexts else f"{lbl} is a key concept identified in the document."
            
            enriched_terms.append({
                "id": str(i),
                "label": lbl,
                "term_key": term_key,
                "category": category,
                "color": ConceptCategorizer.get_color(category),
                "frequency": item["frequency"],
                "tfidf_score": item["tfidf_score"],
                "importance_score": item["composite_score"],
                "definition": definition,
                "contexts": contexts
            })

        return enriched_terms
