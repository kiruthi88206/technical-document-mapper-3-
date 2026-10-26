import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from .similarity import SemanticSimilarity

RELATIONSHIP_VERB_PATTERNS = [
    (r'\b(?:uses|utilizes|leverages|applies|employs)\b', "uses"),
    (r'\b(?:implements|realizes|constructs|builds)\b', "implements"),
    (r'\b(?:part of|component of|module of|subsystem of|contains|includes)\b', "part of"),
    (r'\b(?:depends on|relies on|requires|needs)\b', "depends on"),
    (r'\b(?:stores|persists|manages|caches)\b', "stores"),
    (r'\b(?:produces|generates|outputs|creates|yields)\b', "produces"),
    (r'\b(?:measures|evaluates|calculates|computes|ranks)\b', "evaluates"),
    (r'\b(?:visualizes|renders|displays|presents)\b', "visualizes"),
    (r'\b(?:maps to|transforms into|translates to|connects to)\b', "connects to"),
    (r'\b(?:similar to|equivalent to|corresponds to)\b', "similar to"),
    (r'\b(?:is a|type of|kind of)\b', "is a")
]

class RelationshipDetector:
    """Detects semantic, co-occurrence, and contextual relationships between concepts."""

    @classmethod
    def find_contextual_predicate(cls, sentence: str, term_a: str, term_b: str) -> Tuple[str, str]:
        """Examine the text segment between term_a and term_b for explicit relational predicates."""
        pat_a = re.escape(term_a)
        pat_b = re.escape(term_b)

        # A ... B
        m1 = re.search(rf'\b{pat_a}\b(.*?)\b{pat_b}\b', sentence, re.IGNORECASE)
        # B ... A
        m2 = re.search(rf'\b{pat_b}\b(.*?)\b{pat_a}\b', sentence, re.IGNORECASE)

        target_span = ""
        is_forward = True

        if m1 and len(m1.group(1)) < 120:
            target_span = m1.group(1).lower()
            is_forward = True
        elif m2 and len(m2.group(1)) < 120:
            target_span = m2.group(1).lower()
            is_forward = False

        if target_span:
            for pattern, rel_type in RELATIONSHIP_VERB_PATTERNS:
                if re.search(pattern, target_span):
                    return rel_type, ("forward" if is_forward else "backward")

        return "relates to", "forward"

    @classmethod
    def detect_relationships(
        cls, 
        concepts: List[Dict[str, Any]], 
        sentences: List[str],
        similarity_threshold: float = 0.65
    ) -> List[Dict[str, Any]]:
        """
        Detect multi-dimensional relationships:
        1. Explicit sentence-level co-occurrence with verb predicates
        2. Window-based paragraph proximity
        3. High semantic embedding similarity
        """
        if not concepts or len(concepts) < 2:
            return []

        concept_map = {c["id"]: c for c in concepts}
        term_to_id = {c["label"].lower(): c["id"] for c in concepts}
        labels = [c["label"] for c in concepts]

        # Compile regex searchers for each concept
        concept_patterns = {
            c["id"]: re.compile(rf'\b{re.escape(c["label"])}\b', re.IGNORECASE)
            for c in concepts
        }

        # 1. Co-occurrence matrix across sentences
        co_occurrences = defaultdict(lambda: {"count": 0, "sentences": [], "predicates": []})

        for sent in sentences:
            present_ids = []
            for cid, pat in concept_patterns.items():
                if pat.search(sent):
                    present_ids.append(cid)

            # Record pairwise co-occurrence
            if len(present_ids) >= 2:
                for i in range(len(present_ids)):
                    for j in range(i + 1, len(present_ids)):
                        id1, id2 = sorted([present_ids[i], present_ids[j]])
                        term1 = concept_map[id1]["label"]
                        term2 = concept_map[id2]["label"]

                        pred, direction = cls.find_contextual_predicate(sent, term1, term2)
                        
                        pair_key = (id1, id2)
                        co_occurrences[pair_key]["count"] += 1
                        if len(co_occurrences[pair_key]["sentences"]) < 3:
                            co_occurrences[pair_key]["sentences"].append(sent)
                        co_occurrences[pair_key]["predicates"].append(pred)

        # 2. Semantic similarity matrix
        sim_matrix = SemanticSimilarity.compute_similarity_matrix(labels)

        # 3. Formulate graph edges
        edges = []
        edge_set = set()
        edge_counter = 1

        # Process Co-occurrence edges first
        for (id1, id2), data in co_occurrences.items():
            count = data["count"]
            predicates = data["predicates"]
            # Pick most specific predicate if available
            specific_preds = [p for p in predicates if p != "relates to"]
            rel_label = specific_preds[0] if specific_preds else "relates to"
            
            # Confidence calculation based on occurrences
            confidence = min(0.98, round(0.50 + 0.12 * count, 2))
            
            edge = {
                "id": f"e{edge_counter}",
                "from": id1,
                "to": id2,
                "label": rel_label,
                "type": "co-occurrence",
                "weight": count,
                "confidence": confidence,
                "evidence": data["sentences"][0] if data["sentences"] else "Co-occurs within document context.",
                "all_evidence": data["sentences"]
            }
            edges.append(edge)
            edge_set.add((id1, id2))
            edge_set.add((id2, id1))
            edge_counter += 1

        # Process Semantic Similarity edges
        if sim_matrix is not None:
            n = len(concepts)
            for i in range(n):
                for j in range(i + 1, n):
                    id1 = concepts[i]["id"]
                    id2 = concepts[j]["id"]
                    if (id1, id2) in edge_set:
                        # Already connected by co-occurrence; optionally boost confidence
                        continue

                    sim_score = float(sim_matrix[i, j])
                    if sim_score >= similarity_threshold:
                        edge = {
                            "id": f"e{edge_counter}",
                            "from": id1,
                            "to": id2,
                            "label": "semantically similar",
                            "type": "semantic-similarity",
                            "weight": round(sim_score, 2),
                            "confidence": round(sim_score, 2),
                            "evidence": f"High semantic vector similarity ({sim_score:.2f}) between concepts.",
                            "all_evidence": []
                        }
                        edges.append(edge)
                        edge_set.add((id1, id2))
                        edge_set.add((id2, id1))
                        edge_counter += 1

        # 4. Fallback connections for isolated high-importance nodes
        # Per project requirements: If relationships cannot be confidently detected,
        # clearly identify any fallback connections so the graph is never blank,
        # but honestly label them as "topical proximity (contextual fallback)".
        connected_node_ids = set()
        for e in edges:
            connected_node_ids.add(e["from"])
            connected_node_ids.add(e["to"])

        unconnected_nodes = [c for c in concepts if c["id"] not in connected_node_ids]
        
        # If the graph has isolated nodes or no edges at all:
        if (len(edges) == 0 or len(unconnected_nodes) > 0) and len(concepts) >= 2:
            # Connect top concept or nearest category neighbor
            anchor_node = concepts[0] # Highest ranked concept
            
            for isolated in unconnected_nodes:
                if isolated["id"] == anchor_node["id"]:
                    continue
                
                # Find nearest same-category or anchor
                target_node = anchor_node
                same_cat = [c for c in concepts if c["category"] == isolated["category"] and c["id"] != isolated["id"] and c["id"] in connected_node_ids]
                if same_cat:
                    target_node = same_cat[0]

                edge = {
                    "id": f"e{edge_counter}",
                    "from": target_node["id"],
                    "to": isolated["id"],
                    "label": "contextual link",
                    "type": "contextual-fallback",
                    "weight": 1,
                    "confidence": 0.35,
                    "evidence": "Shared topical context within the technical document.",
                    "all_evidence": []
                }
                edges.append(edge)
                edge_counter += 1
                connected_node_ids.add(isolated["id"])

        return edges
