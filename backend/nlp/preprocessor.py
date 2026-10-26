import re
from typing import List, Dict, Any, Tuple

# Try loading spaCy
_nlp = None
try:
    import spacy
    try:
        _nlp = spacy.load("en_core_web_sm")
    except Exception:
        # Fallback to blank model with sentencizer
        _nlp = spacy.blank("en")
        _nlp.add_pipe("sentencizer")
except Exception:
    _nlp = None

# Fallback stopwords
COMMON_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
    "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers",
    "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in",
    "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll",
    "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their",
    "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "also", "using", "use", "used", "uses", "via", "various", "based",
    "provides", "provide", "provided", "different", "system", "systems", "figure", "table", "section",
    "et", "al", "paper", "presents", "presented", "study", "results", "approach", "shown", "show", "shows"
}

class Preprocessor:
    """Preprocesses text for NLP, sentence splitting, and tokenization."""

    @classmethod
    def get_spacy_nlp(cls):
        return _nlp

    @classmethod
    def split_sentences(cls, text: str) -> List[str]:
        """Split document text into clean, individual sentences."""
        if not text:
            return []

        if _nlp is not None:
            doc = _nlp(text[:500000]) # Cap to avoid out-of-memory on gigantic files
            sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 8]
            if sentences:
                return sentences

        # Regex fallback
        raw_sents = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text)
        clean = []
        for s in raw_sents:
            s_clean = s.strip()
            if len(s_clean) > 8 and not s_clean.startswith(('---', '===', '___')):
                clean.append(s_clean)
        return clean

    @classmethod
    def tokenize(cls, sentence: str) -> List[str]:
        """Tokenize sentence into lower-case alphanumeric words."""
        tokens = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_-]*\b', sentence.lower())
        return [t for t in tokens if t not in COMMON_STOPWORDS and len(t) > 2]
