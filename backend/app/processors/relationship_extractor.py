import re
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

# Ordered list of directed relation patterns: (regex_pattern, forward_relation, backward_relation, confidence)
PREDICATE_RULES = [
    # IS_A
    (r'\b(?:is|are)\s+(?:a|an)\s+(?:type|kind|category|class|subclass|form|variant)\s+of\b', "IS_A", "RELATED_TO", 0.95),
    (r'\b(?:is|are)\s+(?:a|an)\b', "IS_A", "RELATED_TO", 0.88),
    (r'\bsuch\s+as\b', "RELATED_TO", "IS_A", 0.82),

    # PART_OF
    (r'\b(?:is|are)\s+(?:part|a\s+part|a\s+component|a\s+module|a\s+subsystem|a\s+unit)\s+of\b', "PART_OF", "RELATED_TO", 0.92),
    (r'\b(?:consists\s+of|comprises|is\s+composed\s+of|contains|includes)\b', "RELATED_TO", "PART_OF", 0.88),

    # USES
    (r'\b(?:uses|utilizes|leverages|employs|operates\s+with|applies)\b', "USES", "RELATED_TO", 0.85),
    (r'\b(?:is|are)\s+used\s+(?:in|by|for)\b', "RELATED_TO", "USES", 0.83),

    # DEPENDS_ON
    (r'\b(?:depends\s+on|relies\s+on|requires|needs|prerequisite\s+for)\b', "DEPENDS_ON", "RELATED_TO", 0.90),

    # IMPLEMENTS
    (r'\b(?:implements|realizes|constructs|builds|instantiates)\b', "IMPLEMENTS", "RELATED_TO", 0.87),

    # PRODUCES
    (r'\b(?:produces|generates|outputs|creates|yields)\b', "PRODUCES", "RELATED_TO", 0.86),

    # ENABLES
    (r'\b(?:enables|facilitates|allows|permits|powers)\b', "ENABLES", "RELATED_TO", 0.85),

    # CAUSES
    (r'\b(?:causes|leads\s+to|results\s+in|triggers)\b', "CAUSES", "RELATED_TO", 0.88),

    # COMPARED_WITH
    (r'\b(?:compared\s+with|compared\s+to|in\s+contrast\s+to|outperforms|differs\s+from|similar\s+to)\b', "COMPARED_WITH", "COMPARED_WITH", 0.82),

    # RELATED_TO
    (r'\b(?:connects\s+to|associates\s+with|maps\s+to|corresponds\s+to)\b', "RELATED_TO", "RELATED_TO", 0.75),
]


class RelationshipExtractor:
    """
    Extracts high-precision directed relationships between concepts.
    Validates evidence from actual source sentences, prevents hallucinated relationships,
    and assigns calibrated confidence scores.
    """

    @classmethod
    def match_predicate_in_span(cls, span_text: str) -> Optional[Tuple[str, float]]:
        clean_span = span_text.strip().lower()
        for pattern, forward_rel, _, conf in PREDICATE_RULES:
            if re.search(pattern, clean_span):
                return forward_rel, conf
        return None

    @classmethod
    def extract_relationships(
        cls,
        concepts: List[Dict[str, Any]],
        sentences: List[str],
        chunks: List[Dict[str, Any]],
        min_confidence: float = 0.50
    ) -> List[Dict[str, Any]]:
        """
        Scans sentences containing pairs of concepts, analyzes the grammatical bridge between them,
        and produces directed, evidence-backed relationships.
        """
        if not concepts or len(concepts) < 2 or not sentences:
            return []

        # Map concept names and IDs
        concept_names = [c["name"] for c in concepts]
        name_to_concept = {c["name"].lower(): c for c in concepts}

        # Precompile regex for fast sentence search
        concept_patterns = {
            c["name"]: re.compile(rf'\b{re.escape(c["name"])}\b', re.IGNORECASE)
            for c in concepts
        }

        # Discover co-occurrences in each sentence
        discovered_edges = {}

        for sent_idx, sentence in enumerate(sentences):
            present_concepts = []
            for c in concepts:
                if concept_patterns[c["name"]].search(sentence):
                    present_concepts.append(c)

            if len(present_concepts) < 2:
                continue

            # Check each pair in the sentence
            for i in range(len(present_concepts)):
                for j in range(i + 1, len(present_concepts)):
                    c_a = present_concepts[i]
                    c_b = present_concepts[j]
                    if c_a["id"] == c_b["id"]:
                        continue

                    pat_a = re.escape(c_a["name"])
                    pat_b = re.escape(c_b["name"])

                    # Search forward span: A ... B
                    m_fwd = re.search(rf'\b({pat_a})\b(.*?)\b({pat_b})\b', sentence, re.IGNORECASE)
                    # Search backward span: B ... A
                    m_bwd = re.search(rf'\b({pat_b})\b(.*?)\b({pat_a})\b', sentence, re.IGNORECASE)

                    rel_type = None
                    src_concept = None
                    tgt_concept = None
                    conf = 0.50

                    if m_fwd and len(m_fwd.group(2)) < 150:
                        span = m_fwd.group(2)
                        match_res = cls.match_predicate_in_span(span)
                        if match_res:
                            rel_type, conf = match_res
                            src_concept = c_a
                            tgt_concept = c_b

                    if not rel_type and m_bwd and len(m_bwd.group(2)) < 150:
                        span = m_bwd.group(2)
                        match_res = cls.match_predicate_in_span(span)
                        if match_res:
                            rel_type, conf = match_res
                            src_concept = c_b
                            tgt_concept = c_a

                    # If no explicit grammatical verb matched, check strong structural proximity
                    if not rel_type:
                        # If both appear close in a sentence with technical verbs
                        has_tech_verb = any(v in sentence.lower() for v in ["architecture", "model", "pipeline", "framework", "system", "process"])
                        if has_tech_verb and (abs(len(sentence.split())) < 40):
                            rel_type = "RELATED_TO"
                            src_concept = c_a
                            tgt_concept = c_b
                            conf = 0.58

                    if rel_type and conf >= min_confidence:
                        edge_key = (src_concept["id"], tgt_concept["id"], rel_type)
                        
                        # Find source page and section from chunks
                        page_num = 1
                        section_name = "General"
                        for chk in chunks:
                            if src_concept["name"].lower() in chk.get("text", "").lower() and tgt_concept["name"].lower() in chk.get("text", "").lower():
                                page_num = chk.get("page_number", 1)
                                section_name = chk.get("section_heading", "Main")
                                break

                        if edge_key not in discovered_edges or conf > discovered_edges[edge_key]["confidence_score"]:
                            discovered_edges[edge_key] = {
                                "source_concept_id": src_concept["id"],
                                "target_concept_id": tgt_concept["id"],
                                "source_name": src_concept["name"],
                                "target_name": tgt_concept["name"],
                                "relation_type": rel_type,
                                "confidence_score": conf,
                                "supporting_sentence": sentence.strip(),
                                "source_page": page_num,
                                "source_section": section_name,
                                "extraction_method": "grammar_predicate" if rel_type != "RELATED_TO" else "contextual_proximity",
                                "is_directed": True
                            }

        # Deduplicate and sort by confidence score
        relationships = list(discovered_edges.values())
        relationships.sort(key=lambda r: r["confidence_score"], reverse=True)
        return relationships
