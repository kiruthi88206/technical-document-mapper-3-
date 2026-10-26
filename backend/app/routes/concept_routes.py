from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from ..database import get_db
from ..models import Concept, Relationship

concept_bp = Blueprint("concepts", __name__, url_prefix="/api/concepts")

@concept_bp.route("", methods=["GET"])
def list_concepts():
    """
    GET /api/concepts
    Query params: document_id, category, search, min_confidence, page, limit
    """
    session = get_db()
    doc_id = request.args.get("document_id")
    category = request.args.get("category")
    search = request.args.get("search", "").strip()
    min_confidence = request.args.get("min_confidence", type=float)
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 100, type=int)

    query = session.query(Concept)

    if doc_id:
        query = query.filter(Concept.document_id == doc_id)
    if category:
        query = query.filter(Concept.category == category)
    if search:
        search_pat = f"%{search}%"
        query = query.filter(
            or_(
                Concept.name.ilike(search_pat),
                Concept.normalized_name.ilike(search_pat),
                Concept.definition.ilike(search_pat)
            )
        )
    if min_confidence is not None:
        query = query.filter(Concept.confidence_score >= min_confidence)

    query = query.order_by(Concept.confidence_score.desc())
    total = query.count()
    concepts = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "success": True,
        "total": total,
        "page": page,
        "limit": limit,
        "concepts": [c.to_dict() for c in concepts]
    })


@concept_bp.route("/<concept_id>", methods=["GET"])
def get_concept(concept_id):
    """
    GET /api/concepts/<concept_id>
    """
    session = get_db()
    c = session.query(Concept).filter_by(id=concept_id).first()
    if not c:
        return jsonify({"error": f"Concept '{concept_id}' not found.", "status": 404}), 404

    return jsonify({"success": True, "concept": c.to_dict()})


@concept_bp.route("/<concept_id>/relationships", methods=["GET"])
def get_concept_relationships(concept_id):
    """
    GET /api/concepts/<concept_id>/relationships
    Returns incoming and outgoing relationships with source sentence and confidence.
    """
    session = get_db()
    c = session.query(Concept).filter_by(id=concept_id).first()
    if not c:
        return jsonify({"error": f"Concept '{concept_id}' not found.", "status": 404}), 404

    outgoing = [r.to_dict() for r in c.outgoing_relationships]
    incoming = [r.to_dict() for r in c.incoming_relationships]

    return jsonify({
        "success": True,
        "concept_id": c.id,
        "concept_name": c.name,
        "outgoing": outgoing,
        "incoming": incoming,
        "total_connections": len(outgoing) + len(incoming)
    })
