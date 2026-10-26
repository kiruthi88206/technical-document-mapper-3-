from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc, asc
from ..database import get_db
from ..models import Terminology, Concept, Relationship

terminology_bp = Blueprint("terminology", __name__, url_prefix="/api/terminology")

@terminology_bp.route("", methods=["GET"])
def list_terminology():
    """
    GET /api/terminology
    Query params:
    - document_id (optional)
    - search (optional query string)
    - min_confidence (optional float)
    - definition_type (optional filter)
    - sort_by (frequency, confidence_score, term)
    - order (asc, desc)
    - page, limit
    """
    session = get_db()
    doc_id = request.args.get("document_id")
    search_query = request.args.get("search", "").strip()
    min_confidence = request.args.get("min_confidence", type=float)
    def_type = request.args.get("definition_type")
    sort_by = request.args.get("sort_by", "frequency")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)

    query = session.query(Terminology)

    if doc_id:
        query = query.filter(Terminology.document_id == doc_id)

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Terminology.term.ilike(search_pattern),
                Terminology.normalized_term.ilike(search_pattern),
                Terminology.definition.ilike(search_pattern)
            )
        )

    if min_confidence is not None:
        query = query.filter(Terminology.confidence_score >= min_confidence)

    if def_type:
        query = query.filter(Terminology.definition_type == def_type)

    # Sorting
    sort_column = getattr(Terminology, sort_by, Terminology.frequency)
    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    total = query.count()
    terms = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "success": True,
        "total": total,
        "page": page,
        "limit": limit,
        "terminology": [t.to_dict() for t in terms]
    })


@terminology_bp.route("/<term_id>", methods=["GET"])
def get_term(term_id):
    """
    GET /api/terminology/<term_id>
    Retrieve term details with associated concepts and relations.
    """
    session = get_db()
    term = session.query(Terminology).filter_by(id=term_id).first()
    if not term:
        return jsonify({"error": f"Terminology entry '{term_id}' not found.", "status": 404}), 404

    result = term.to_dict()

    # Find matching concept
    concept = session.query(Concept).filter_by(
        document_id=term.document_id,
        normalized_name=term.normalized_term
    ).first()

    related_concepts = []
    if concept:
        # Outgoing
        for rel in concept.outgoing_relationships:
            related_concepts.append({
                "relation_id": rel.id,
                "direction": "outgoing",
                "relation_type": rel.relation_type,
                "target_concept_id": rel.target_concept_id,
                "target_name": rel.target_concept.name if rel.target_concept else "Unknown",
                "confidence_score": rel.confidence_score,
                "supporting_sentence": rel.supporting_sentence
            })
        # Incoming
        for rel in concept.incoming_relationships:
            related_concepts.append({
                "relation_id": rel.id,
                "direction": "incoming",
                "relation_type": rel.relation_type,
                "source_concept_id": rel.source_concept_id,
                "source_name": rel.source_concept.name if rel.source_concept else "Unknown",
                "confidence_score": rel.confidence_score,
                "supporting_sentence": rel.supporting_sentence
            })

    result["related_concepts"] = related_concepts
    return jsonify({"success": True, "term": result})
