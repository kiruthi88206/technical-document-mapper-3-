import math
from collections import Counter
from flask import Blueprint, request, jsonify
import networkx as nx
from ..database import get_db
from ..models import Document, Concept, Relationship

graph_bp = Blueprint("graph", __name__, url_prefix="/api/documents")

CATEGORY_COLORS = {
    "Architecture": "#0ea5e9",       # sky blue
    "Model & Learning": "#6366f1",   # indigo
    "Data & Storage": "#10b981",     # emerald green
    "Algorithm & Logic": "#f59e0b",   # amber
    "Evaluation & Metric": "#ec4899", # pink
    "Component & System": "#8b5cf6", # violet
    "General Concept": "#64748b"     # slate
}

RELATION_COLORS = {
    "IS_A": "#3b82f6",          # blue
    "PART_OF": "#10b981",       # emerald
    "USES": "#8b5cf6",          # purple
    "DEPENDS_ON": "#ef4444",    # red
    "PRODUCES": "#f97316",      # orange
    "IMPLEMENTS": "#06b6d4",    # cyan
    "ENABLES": "#14b8a6",       # teal
    "CAUSES": "#e11d48",        # rose
    "COMPARED_WITH": "#a855f7", # purple-accent
    "RELATED_TO": "#64748b"     # neutral slate
}

@graph_bp.route("/<document_id>/graph", methods=["GET"])
def get_document_graph(document_id):
    """
    GET /api/documents/<document_id>/graph
    Returns full node and edge topology optimized for React Flow rendering,
    including calculated layout positions, node metrics, edge evidence, and network statistics.
    """
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    concepts = session.query(Concept).filter_by(document_id=doc.id).all()
    relationships = session.query(Relationship).filter_by(document_id=doc.id).all()

    if not concepts:
        return jsonify({
            "success": True,
            "document_id": doc.id,
            "document_name": doc.original_filename,
            "nodes": [],
            "edges": [],
            "metrics": {
                "nodes_count": 0,
                "edges_count": 0,
                "density": 0.0,
                "primary_hub": "None",
                "categories": {},
                "relationship_types": {}
            }
        })

    # Build NetworkX graph for spring layout positioning & centrality
    G = nx.DiGraph()
    for c in concepts:
        G.add_node(c.id, name=c.name)
    for r in relationships:
        G.add_edge(r.source_concept_id, r.target_concept_id)

    # Compute 2D layout positions
    try:
        # Scale positions with ample breathing room for larger, clear concept cards
        if len(concepts) > 1:
            raw_pos = nx.spring_layout(G, k=2.5 / math.sqrt(len(concepts)), iterations=70, seed=42)
        else:
            raw_pos = {concepts[0].id: (0.0, 0.0)}
    except Exception:
        raw_pos = {c.id: (0.0, 0.0) for c in concepts}

    # Count node connections
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())

    # Format React Flow nodes
    nodes = []
    category_counter = Counter()

    for idx, c in enumerate(concepts):
        x, y = raw_pos.get(c.id, (0.0, 0.0))
        # Generously spaced coordinates for clear visibility
        pos_x = round(float(x) * 850 + 750, 1)
        pos_y = round(float(y) * 600 + 500, 1)

        cat = c.category or "General Concept"
        category_counter[cat] += 1
        color = CATEGORY_COLORS.get(cat, "#6366f1")

        in_count = in_degree.get(c.id, 0)
        out_count = out_degree.get(c.id, 0)

        nodes.append({
            "id": c.id,
            "type": "conceptNode",
            "position": {"x": pos_x, "y": pos_y},
            "data": {
                "id": c.id,
                "label": c.name,
                "category": cat,
                "color": color,
                "frequency": c.frequency,
                "confidence_score": c.confidence_score,
                "centrality_score": c.centrality_score,
                "definition": c.definition or "No explicit definition found.",
                "description": c.description or "",
                "incoming_count": in_count,
                "outgoing_count": out_count,
                "document_id": c.document_id,
            }
        })

    # Format React Flow directed edges
    edges = []
    relation_counter = Counter()

    for r in relationships:
        rel_type = r.relation_type or "RELATED_TO"
        relation_counter[rel_type] += 1
        edge_color = RELATION_COLORS.get(rel_type, "#475569")

        src_name = r.source_concept.name if r.source_concept else "Unknown"
        tgt_name = r.target_concept.name if r.target_concept else "Unknown"

        edges.append({
            "id": r.id,
            "source": r.source_concept_id,
            "target": r.target_concept_id,
            "type": "smoothstep",
            "animated": True,
            "label": rel_type,
            "style": {
                "stroke": edge_color,
                "strokeWidth": 2.5,
            },
            "labelStyle": {
                "fill": edge_color,
                "fontWeight": 700,
                "fontSize": 12,
            },
            "labelBgStyle": {
                "fill": "#ffffff",
                "fillOpacity": 0.95,
                "rx": 6,
                "ry": 6,
            },
            "labelBgPadding": [6, 4],
            "markerEnd": {
                "type": "arrowclosed",
                "color": edge_color,
                "width": 18,
                "height": 18,
            },
            "data": {
                "id": r.id,
                "relation_type": rel_type,
                "confidence_score": r.confidence_score,
                "supporting_sentence": r.supporting_sentence,
                "source_page": r.source_page,
                "source_section": r.source_section,
                "extraction_method": r.extraction_method,
                "source_name": src_name,
                "target_name": tgt_name,
                "color": edge_color
            }
        })

    # Calculate graph summary metrics
    density = nx.density(G) if len(concepts) > 1 else 0.0
    primary_hub = "None"
    if concepts:
        hub_concept = max(concepts, key=lambda c: in_degree.get(c.id, 0) + out_degree.get(c.id, 0))
        primary_hub = hub_concept.name

    return jsonify({
        "success": True,
        "document_id": doc.id,
        "document_name": doc.original_filename,
        "nodes": nodes,
        "edges": edges,
        "metrics": {
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "density": round(float(density), 3),
            "primary_hub": primary_hub,
            "categories": dict(category_counter),
            "relationship_types": dict(relation_counter),
            "category_colors": CATEGORY_COLORS,
            "relation_colors": RELATION_COLORS
        }
    })
