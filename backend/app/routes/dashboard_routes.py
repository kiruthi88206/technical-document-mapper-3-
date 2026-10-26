from flask import Blueprint, jsonify
from sqlalchemy import func
from ..database import get_db
from ..models import Document, Terminology, Concept, Relationship, ProcessingJob

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

@dashboard_bp.route("/stats", methods=["GET"])
def get_dashboard_stats():
    """
    GET /api/dashboard/stats
    Returns aggregated real database statistics for the dashboard.
    """
    session = get_db()

    total_docs = session.query(func.count(Document.id)).scalar() or 0
    total_processed_docs = session.query(func.count(Document.id)).filter(
        Document.status.in_(["completed", "completed_with_warnings"])
    ).scalar() or 0
    total_terms = session.query(func.count(Terminology.id)).scalar() or 0
    total_concepts = session.query(func.count(Concept.id)).scalar() or 0
    total_relationships = session.query(func.count(Relationship.id)).scalar() or 0

    # Recent documents
    recent_docs = session.query(Document).order_by(Document.upload_date.desc()).limit(5).all()

    # Recent processing activities
    recent_jobs = session.query(ProcessingJob).order_by(ProcessingJob.updated_at.desc()).limit(6).all()

    # Category distribution for chart
    categories_query = session.query(
        Concept.category, func.count(Concept.id)
    ).group_by(Concept.category).all()
    categories_dist = {cat: count for cat, count in categories_query if cat}

    # Relationship type distribution for chart
    rel_types_query = session.query(
        Relationship.relation_type, func.count(Relationship.id)
    ).group_by(Relationship.relation_type).all()
    rel_types_dist = {rel: count for rel, count in rel_types_query if rel}

    return jsonify({
        "success": True,
        "metrics": {
            "total_documents": total_docs,
            "total_processed_documents": total_processed_docs,
            "total_terminology": total_terms,
            "total_concepts": total_concepts,
            "total_relationships": total_relationships,
        },
        "recent_documents": [d.to_dict() for d in recent_docs],
        "recent_activity": [j.to_dict() for j in recent_jobs],
        "analytics": {
            "categories_distribution": categories_dist,
            "relationship_types_distribution": rel_types_dist
        }
    })
