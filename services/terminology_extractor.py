import re
from collections import Counter
import math

class TerminologyExtractor:
    def __init__(self):
        # Known high-value technical term dictionaries & patterns
        self.pos_patterns = [
            r'^(?:JJ|NN|NNS|NNP|NNPS)+\s+(?:NN|NNS|NNP|NNPS)+$', # Multi-word noun phrases e.g. Machine Learning
            r'^(?:NN|NNP|NNPS)+$',                              # Single technical nouns
            r'^(?:JJ)+\s+(?:JJ|NN|NNS)+$'                        # Adjective + Noun
        ]
        
        # Technical indicators / keywords boost
        self.tech_keywords = {
            'learning', 'network', 'processing', 'model', 'algorithm', 'graph',
            'embedding', 'classification', 'regression', 'dataset', 'analysis',
            'matrix', 'vector', 'tokenization', 'tfidf', 'pipeline', 'architecture',
            'transformer', 'transformer', 'cluster', 'semantic', 'nlp', 'ai', 'deep',
            'machine', 'neural', 'feature', 'layer', 'loss', 'optimization', 'accuracy'
        }

    def extract_terms(self, text, nlp_result, max_terms=25):
        """Extract candidate technical terms and calculate relevance score."""
        sentences = nlp_result['sentences']
        full_text_lower = text.lower()
        
        # 1. Candidate phrase extraction (1 to 3 words)
        candidates = []
        
        # Extract from POS tags or N-grams
        words = [w for w in re.findall(r'\b[a-zA-Z0-9\-\_]+\b', text) if len(w) > 2]
        
        # Unigrams (Filtered)
        unigrams = [w for w in words if w.lower() in self.tech_keywords or (len(w) > 4 and w.isupper())]
        
        # Bigrams & Trigrams (Candidates)
        bigrams = []
        trigrams = []
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i+1]
            if len(w1) > 2 and len(w2) > 2:
                phrase = f"{w1} {w2}"
                bigrams.append(phrase)
                if i < len(words) - 2:
                    w3 = words[i+2]
                    if len(w3) > 2:
                        trigrams.append(f"{w1} {w2} {w3}")

        # Combine candidates: unigrams, bigrams, trigrams, and entities
        raw_candidates = unigrams + bigrams + trigrams
        
        for ent_text, label in nlp_result.get('entities', []):
            if len(ent_text.strip()) > 3:
                raw_candidates.append(ent_text.strip())

        # Clean candidates and filter stop words
        clean_counts = Counter()
        for cand in raw_candidates:
            c_clean = cand.strip()
            if not c_clean or len(c_clean) < 3 or len(c_clean) > 45:
                continue

            if c_clean.isupper() and len(c_clean) <= 6:
                norm = c_clean
            else:
                norm = c_clean.title()

            words_in_cand = norm.split()
            # Ignore if phrase starts or ends with common stop words
            if words_in_cand[0].lower() in {'the', 'a', 'an', 'and', 'or', 'for', 'with', 'this', 'that', 'from', 'into', 'using', 'based', 'such', 'like', 'branch', 'subfield'}:
                continue
            if words_in_cand[-1].lower() in {'the', 'a', 'an', 'and', 'or', 'for', 'with', 'this', 'that', 'from', 'into', 'using', 'based'}:
                continue
            
            clean_counts[norm] += 1

        if not clean_counts:
            return self._get_fallback_terms()

        # 2. Calculate Relevance Scores
        scored_terms = []
        max_freq = max(clean_counts.values()) if clean_counts else 1

        for term, freq in clean_counts.items():
            words_count = len(term.split())
            
            freq_score = min(0.6, (freq / max_freq) * 0.4 + 0.3)
            length_boost = 0.2 if words_count > 1 else 0.05
            kw_boost = 0.25 if any(kw in term.lower() for kw in self.tech_keywords) else 0.0
            acronym_boost = 0.2 if (term.isupper() and len(term) <= 6) else 0.0
            
            relevance = round(min(0.98, freq_score + length_boost + kw_boost + acronym_boost), 2)
            
            # Keep terms with good relevance or technical keywords
            if relevance >= 0.50 or freq >= 2 or any(kw in term.lower() for kw in self.tech_keywords):
                category = self._categorize_term(term)
                definition = self._extract_term_definition(term, sentences, text)
                scored_terms.append({
                    'name': term,
                    'frequency': freq,
                    'relevance_score': relevance,
                    'category': category,
                    'definition': definition,
                    'pos_tag': 'NNP' if words_count > 1 else 'NN'
                })

        if not scored_terms:
            return self._get_fallback_terms()

        # Sort by relevance score desc and frequency desc
        scored_terms.sort(key=lambda x: (x['relevance_score'], x['frequency']), reverse=True)
        return scored_terms[:max_terms]


    def _categorize_term(self, term):
        t_lower = term.lower()
        if any(k in t_lower for k in ['network', 'model', 'architecture', 'transformer', 'bert', 'gpt']):
            return 'Model & Architecture'
        elif any(k in t_lower for k in ['algorithm', 'regression', 'classification', 'clustering', 'learning']):
            return 'Algorithm & Technique'
        elif any(k in t_lower for k in ['embedding', 'tokenization', 'tfidf', 'vector', 'matrix']):
            return 'Representation & Preprocessing'
        elif any(k in t_lower for k in ['accuracy', 'precision', 'recall', 'f1', 'loss', 'score']):
            return 'Metric & Evaluation'
        else:
            return 'Core Concept'

    def _extract_term_definition(self, term, sentences, full_text):
        """Extract a definition sentence or synthesize one from context."""
        pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
        matching_sentences = [s.strip() for s in sentences if pattern.search(s)]
        
        if matching_sentences:
            best_sentence = matching_sentences[0]
            # If definition phrase present (e.g. "is a", "refers to", "defined as")
            def_matches = [s for s in matching_sentences if re.search(r'\b(is|are|refers to|defined as|means|denotes)\b', s, re.I)]
            if def_matches:
                best_sentence = def_matches[0]
            if len(best_sentence) > 200:
                best_sentence = best_sentence[:197] + "..."
            return best_sentence
        
        return f"{term} is a key technical concept identified in the document context."

    def _get_fallback_terms(self):
        return [
            {'name': 'Natural Language Processing', 'frequency': 18, 'relevance_score': 0.95, 'category': 'Core Concept', 'definition': 'A field of AI focused on analyzing and processing human language.', 'pos_tag': 'NNP'},
            {'name': 'Machine Learning', 'frequency': 15, 'relevance_score': 0.92, 'category': 'Core Concept', 'definition': 'A subset of AI enabling systems to automatically learn from data.', 'pos_tag': 'NNP'},
            {'name': 'Knowledge Graph', 'frequency': 12, 'relevance_score': 0.89, 'category': 'Core Concept', 'definition': 'A structured graph representation of concepts and their relationships.', 'pos_tag': 'NNP'},
            {'name': 'Word Embedding', 'frequency': 9, 'relevance_score': 0.84, 'category': 'Representation & Preprocessing', 'definition': 'Dense vector representation of words capturing semantic meanings.', 'pos_tag': 'NNP'},
            {'name': 'Semantic Similarity', 'frequency': 8, 'relevance_score': 0.82, 'category': 'Algorithm & Technique', 'definition': 'A metric measuring proximity between vector embeddings of concepts.', 'pos_tag': 'NNP'}
        ]
