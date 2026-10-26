import re
import nltk

# Download essential NLTK packages if needed
for resource in ['punkt', 'punkt_tab', 'stopwords', 'wordnet', 'averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng']:
    try:
        nltk.download(resource, quiet=True)
    except Exception:
        pass

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

class NLPProcessor:
    def __init__(self):
        try:
            self.lemmatizer = WordNetLemmatizer()
        except Exception:
            self.lemmatizer = None

        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            self.stop_words = {'the', 'a', 'an', 'in', 'is', 'it', 'of', 'and', 'or', 'to', 'for', 'with', 'on', 'at', 'by', 'this', 'that', 'are', 'was', 'were', 'be', 'been', 'being'}
        
        # Domain specific stop words to ignore
        self.domain_stopwords = {
            'figure', 'table', 'section', 'page', 'author', 'result', 'paper',
            'study', 'method', 'using', 'used', 'based', 'approach', 'system',
            'data', 'model', 'analysis', 'show', 'shown', 'et', 'al', 'etc'
        }

    def process_text(self, text):
        """Full NLP pipeline: sentences, tokens, POS tags, entities, lemmas."""
        sentences = self.split_sentences(text)
        
        # Fast regex word tokenization fallback
        try:
            from nltk.tokenize import word_tokenize
            raw_tokens = word_tokenize(text)
        except Exception:
            raw_tokens = re.findall(r'\b[a-zA-Z0-9\-\_]+\b', text)

        tokens = [t for t in raw_tokens if t.isalnum() or '-' in t]
        
        # POS tag fallback
        try:
            from nltk import pos_tag
            pos_tags = pos_tag(tokens)
        except Exception:
            pos_tags = [(t, 'NN') for t in tokens]

        # Lemma fallback
        if self.lemmatizer:
            try:
                lemmas = [self.lemmatizer.lemmatize(t.lower()) for t in tokens]
            except Exception:
                lemmas = [t.lower() for t in tokens]
        else:
            lemmas = [t.lower() for t in tokens]

        entities = self._extract_nltk_entities(pos_tags)

        filtered_tokens = [
            t for t in tokens 
            if t.lower() not in self.stop_words 
            and t.lower() not in self.domain_stopwords 
            and len(t) > 2
            and re.match(r'^[a-zA-Z0-9\-\_]+$', t)
        ]

        return {
            'sentences': sentences,
            'tokens': tokens,
            'filtered_tokens': filtered_tokens,
            'lemmas': lemmas,
            'pos_tags': pos_tags,
            'entities': entities
        }

    def split_sentences(self, text):
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except Exception:
            return [s.strip() for s in re.split(r'[.!?]+\s+', text) if len(s.strip()) > 5]


    def _extract_nltk_entities(self, pos_tags):
        # Extract proper nouns as candidates
        entities = []
        for word, tag in pos_tags:
            if tag in ['NNP', 'NNPS'] and len(word) > 2:
                entities.append((word, 'CONCEPT'))
        return entities
