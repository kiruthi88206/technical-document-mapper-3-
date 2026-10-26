import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer

COMMON_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more",
    "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's",
    "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they",
    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves", "also", "using", "used", "uses",
    "table", "figure", "section", "chapter", "example", "paper", "author", "approach", "method", "results"
}

_SPACY_NLP = None

def get_spacy_nlp():
    global _SPACY_NLP
    if _SPACY_NLP is False:
        return None
    if _SPACY_NLP is not None:
        return _SPACY_NLP
    try:
        import spacy
        try:
            _SPACY_NLP = spacy.load("en_core_web_sm")
        except Exception:
            _SPACY_NLP = spacy.blank("en")
    except Exception:
        _SPACY_NLP = False
    return _SPACY_NLP if _SPACY_NLP is not False else None


class TerminologyExtractor:
    """
    Extracts, ranks, and categorizes technical terms from document text and chunks.
    Combines linguistic analysis, technical pattern recognition, TF-IDF statistical scoring,
    and case-aware deduplication.
    """

    @classmethod
    def extract_candidates(cls, text: str, sentences: List[str]) -> List[str]:
        candidates = []
        nlp = get_spacy_nlp()

        if nlp is not None:
            try:
                # Process sample chunks if text is long to prevent memory overload
                sample_text = text[:150000]
                doc = nlp(sample_text)
                
                # spaCy noun chunks
                if hasattr(doc, "noun_chunks"):
                    for chunk in doc.noun_chunks:
                        words = chunk.text.strip().split()
                        while words and words[0].lower() in COMMON_STOPWORDS:
                            words.pop(0)
                        while words and words[-1].lower() in COMMON_STOPWORDS:
                            words.pop()
                        if words and 1 <= len(words) <= 4:
                            phrase = " ".join(words)
                            if len(phrase) >= 3 and not phrase.isnumeric():
                                candidates.append(phrase)

                # spaCy named entities (technical/product/org)
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART", "LAW"):
                        c_ent = ent.text.strip()
                        if len(c_ent) >= 3 and c_ent.lower() not in COMMON_STOPWORDS:
                            candidates.append(c_ent)
            except Exception:
                pass

        # Technical Capitalized Terms, Acronyms (e.g. TF-IDF, CNN, BERT, API), Hyphenated terms
        tech_pattern = re.compile(
            r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}|[A-Z]{2,}(?:-[A-Za-z0-9]+)?|[a-zA-Z]+(?:-[a-zA-Z]+)+)\b'
        )
        for sent in sentences:
            # Don't treat first word of sentence as technical term solely because it's capitalized
            words = sent.split()
            first_word = words[0].strip('"\',.?!:;') if words else ""
            matches = tech_pattern.findall(sent)
            for m in matches:
                clean_m = m.strip()
                if clean_m.lower() in COMMON_STOPWORDS or len(clean_m) < 3:
                    continue
                # If single word matches first word and is just Titlecase, skip unless acronym
                if clean_m == first_word and not clean_m.isupper() and "-" not in clean_m:
                    continue
                candidates.append(clean_m)

        # Multi-word technical patterns
        multi_pattern = re.compile(r'\b[a-zA-Z][a-zA-Z0-9_-]*(?:\s+[a-zA-Z][a-zA-Z0-9_-]*){1,2}\b')
        for sent in sentences:
            for phrase in multi_pattern.findall(sent):
                p_lower = phrase.lower()
                p_words = p_lower.split()
                if not any(w in COMMON_STOPWORDS for w in p_words) and len(phrase) >= 5:
                    candidates.append(phrase)

        return candidates

    @classmethod
    def extract_and_rank(
        cls,
        text: str,
        sentences: List[str],
        chunks: List[Dict[str, Any]],
        top_k: int = 40,
        min_freq: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Extracts candidate terms, deduplicates by normalized form, scores via TF-IDF + frequency,
        and attaches source sentence, page number, and section heading.
        """
        if not text or not sentences:
            return []

        raw_candidates = cls.extract_candidates(text, sentences)
        if not raw_candidates:
            return []

        # Count frequencies and preserve variants
        norm_map = defaultdict(list)
        norm_counts = Counter()

        for c in raw_candidates:
            clean = c.strip(" ,.:;()[]{}\"'`")
            if not clean or len(clean) < 3:
                continue
            norm = clean.lower()
            if norm in COMMON_STOPWORDS:
                continue
            norm_map[norm].append(clean)
            norm_counts[norm] += 1

        # TF-IDF across sentences
        valid_vocab = [n for n, cnt in norm_counts.items() if cnt >= min_freq]
        if not valid_vocab:
            valid_vocab = list(norm_counts.keys())[:top_k]

        tfidf_scores = defaultdict(float)
        try:
            vectorizer = TfidfVectorizer(
                vocabulary=valid_vocab,
                lowercase=True,
                stop_words='english',
                ngram_range=(1, 3)
            )
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            dense_scores = tfidf_matrix.sum(axis=0).A1
            for idx, term in enumerate(feature_names):
                tfidf_scores[term] = float(dense_scores[idx])
        except Exception:
            # Fallback heuristic if TF-IDF fails (e.g. short document)
            for term in valid_vocab:
                tfidf_scores[term] = float(norm_counts[term])

        # Normalize TF-IDF max
        max_tfidf = max(tfidf_scores.values()) if tfidf_scores else 1.0
        if max_tfidf == 0:
            max_tfidf = 1.0

        scored_terms = []
        for norm, count in norm_counts.items():
            if count < min_freq and norm not in valid_vocab:
                continue

            # Pick canonical display name (prefer Title Case or Uppercase acronym)
            variants = norm_map[norm]
            canonical = max(set(variants), key=lambda x: (x.isupper(), x.istitle(), variants.count(x), len(x)))

            # Evidence: Find best matching sentence and chunk
            best_sent = ""
            best_page = 1
            best_section = "General"

            pattern = re.compile(rf'\b{re.escape(canonical)}\b', re.IGNORECASE)
            for sent in sentences:
                if pattern.search(sent):
                    best_sent = sent.strip()
                    break

            if not best_sent and sentences:
                best_sent = sentences[0]

            # Find chunk for page and section
            for chk in chunks:
                if pattern.search(chk.get("text", "")):
                    best_page = chk.get("page_number", 1)
                    best_section = chk.get("section_heading", "Main")
                    break

            # Calculate composite confidence score:
            # - Normalized TF-IDF (40%)
            # - Frequency saturation (30%)
            # - Specificity / Multi-word bonus (30%)
            tfidf_norm = tfidf_scores.get(norm, 0.0) / max_tfidf
            freq_score = min(1.0, math.log(count + 1) / math.log(12))
            is_multi = len(canonical.split()) > 1
            is_acronym = canonical.isupper() and len(canonical) >= 2
            spec_score = 0.9 if is_multi else (0.8 if is_acronym else 0.5)

            confidence = round(0.40 * tfidf_norm + 0.30 * freq_score + 0.30 * spec_score, 3)
            # Clip between 0.20 and 0.98
            confidence = max(0.20, min(0.98, confidence))

            scored_terms.append({
                "term": canonical,
                "normalized_term": norm,
                "frequency": count,
                "confidence_score": confidence,
                "extraction_method": "hybrid_pos_tfidf",
                "source_sentence": best_sent,
                "page_number": best_page,
                "section_heading": best_section
            })

        # Sort by confidence descending, then frequency
        scored_terms.sort(key=lambda x: (x["confidence_score"], x["frequency"]), reverse=True)
        return scored_terms[:top_k]
