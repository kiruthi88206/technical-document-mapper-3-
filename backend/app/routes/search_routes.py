from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from ..database import get_db
from ..models import Document, Terminology, Concept, Relationship

search_bp = Blueprint("search", __name__, url_prefix="/api")

@search_bp.route("/search", methods=["GET"])
def global_search():
    """
    GET /api/search?q=<query>
    Searches across:
    - Document names
    - Technical terms & normalized forms
    - Definitions
    - Source sentences/contexts
    - Relationship labels & supporting evidence
    """
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({
            "success": True,
            "query": "",
            "results": {
                "documents": [],
                "terms": [],
                "concepts": [],
                "relationships": []
            },
            "total_matches": 0
        })

    session = get_db()
    pattern = f"%{q}%"

    # 1. Documents matching filename
    matched_docs = session.query(Document).filter(
        or_(
            Document.original_filename.ilike(pattern),
            Document.warning_message.ilike(pattern)
        )
    ).limit(10).all()

    # 2. Terminology matching term or definition or source sentence
    matched_terms = session.query(Terminology).filter(
        or_(
            Terminology.term.ilike(pattern),
            Terminology.normalized_term.ilike(pattern),
            Terminology.definition.ilike(pattern),
            Terminology.source_sentence.ilike(pattern)
        )
    ).limit(30).all()

    # 3. Concepts matching name, category, or definition
    matched_concepts = session.query(Concept).filter(
        or_(
            Concept.name.ilike(pattern),
            Concept.normalized_name.ilike(pattern),
            Concept.category.ilike(pattern),
            Concept.definition.ilike(pattern)
        )
    ).limit(30).all()

    # 4. Relationships matching relation_type or supporting sentence
    matched_relationships = session.query(Relationship).filter(
        or_(
            Relationship.relation_type.ilike(pattern),
            Relationship.supporting_sentence.ilike(pattern)
        )
    ).limit(30).all()

    total_matches = len(matched_docs) + len(matched_terms) + len(matched_concepts) + len(matched_relationships)

    return jsonify({
        "success": True,
        "query": q,
        "total_matches": total_matches,
        "results": {
            "documents": [d.to_dict() for d in matched_docs],
            "terms": [t.to_dict() for t in matched_terms],
            "concepts": [c.to_dict() for c in matched_concepts],
            "relationships": [r.to_dict() for r in matched_relationships]
        }
    })
