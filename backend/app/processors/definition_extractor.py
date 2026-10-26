import re
from typing import List, Dict, Any, Tuple, Optional

# Explicit linguistic definition patterns
DEFINITION_PATTERNS = [
    # "X is defined as Y"
    (r'\b{term}\s+(?:is|are|was|were)\s+defined\s+as\s+([^.;:\n]+)', "explicit_document", 0.95),
    # "X refers to Y"
    (r'\b{term}\s+(?:refers\s+to|describes|denotes)\s+([^.;:\n]+)', "explicit_document", 0.92),
    # "X is a type/form/kind of Y"
    (r'\b{term}\s+(?:is|are)\s+(?:a|an)\s+(?:type|form|kind|category|class)\s+of\s+([^.;:\n]+)', "explicit_document", 0.90),
    # "X is a/an Y which/that ..."
    (r'\b{term}\s+(?:is|are)\s+(?:a|an)\s+([^.;:\n]+)', "explicit_document", 0.88),
    # "X consists of / comprises Y"
    (r'\b{term}\s+(?:consists\s+of|comprises|is\s+composed\s+of)\s+([^.;:\n]+)', "explicit_document", 0.85),
    # "X, which is Y," or "X (meaning Y)"
    (r'\b{term}[,\s]+\s*which\s+(?:is|are)\s+([^,.;:\n]+)', "explicit_document", 0.82),
    (r'\b{term}\s*\((?:i\.e\.|meaning|defined\s+as)?\s*([^)\n]+)\)', "explicit_document", 0.80),
    # "X means Y"
    (r'\b{term}\s+means\s+([^.;:\n]+)', "explicit_document", 0.86),
    # "by X we mean Y"
    (r'by\s+{term}\s*,\s*we\s+mean\s+([^.;:\n]+)', "explicit_document", 0.88),
]

class DefinitionExtractor:
    """
    Extracts explicit definitions and contextual explanations for technical terms.
    Strictly preserves source document truth and marks explicit vs contextual inference.
    """

    @classmethod
    def extract_definition_for_term(
        cls,
        term: str,
        sentences: List[str]
    ) -> Dict[str, Any]:
        """
        Scans document sentences containing the term for explicit definition patterns.
        Falls back to contextual explanatory sentence if no explicit pattern matches.
        """
        escaped_term = re.escape(term)

        # 1. First pass: Search for explicit definition patterns
        for pattern_tmpl, def_type, base_conf in DEFINITION_PATTERNS:
            regex = re.compile(pattern_tmpl.format(term=escaped_term), re.IGNORECASE)
            for sent in sentences:
                match = regex.search(sent)
                if match:
                    extracted_def = match.group(0).strip()
                    # Clean punctuation
                    extracted_def = re.sub(r'\s+', ' ', extracted_def)
                    return {
                        "definition": extracted_def,
                        "definition_type": def_type,
                        "source_sentence": sent.strip(),
                        "confidence": base_conf
                    }

        # 2. Second pass: Search for surrounding explanatory sentence (contextual inference)
        term_word_pat = re.compile(rf'\b{escaped_term}\b', re.IGNORECASE)
        for sent in sentences:
            if term_word_pat.search(sent):
                clean_sent = sent.strip()
                # If the sentence has explanatory cues like 'provides', 'enables', 'serves', 'used for'
                if any(k in clean_sent.lower() for k in ["provides", "enables", "used for", "serves to", "allows", "designed to", "functions as"]):
                    return {
                        "definition": clean_sent,
                        "definition_type": "contextual_inference",
                        "source_sentence": clean_sent,
                        "confidence": 0.72
                    }

        # 3. Third pass: Any primary sentence where term appears
        for sent in sentences:
            if term_word_pat.search(sent):
                clean_sent = sent.strip()
                return {
                    "definition": f"Mentioned in context: \"{clean_sent}\"",
                    "definition_type": "contextual_inference",
                    "source_sentence": clean_sent,
                    "confidence": 0.50
                }

        # 4. Fallback if no sentence matched directly
        return {
            "definition": "Identified as a technical terminology candidate in document text.",
            "definition_type": "contextual_inference",
            "source_sentence": "",
            "confidence": 0.35
        }
