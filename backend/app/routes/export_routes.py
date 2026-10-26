import csv
import io
import json
from flask import Blueprint, request, jsonify, Response, send_file
from ..database import get_db
from ..models import Document, Terminology, Concept, Relationship
from ..services.pdf_report_service import PDFReportService

export_bp = Blueprint("export", __name__, url_prefix="/api/documents")

@export_bp.route("/<document_id>/export/terminology", methods=["GET"])
def export_terminology(document_id):
    """
    GET /api/documents/<document_id>/export/terminology?format=csv|json
    """
    fmt = request.args.get("format", "csv").lower()
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    terms = session.query(Terminology).filter_by(document_id=doc.id).order_by(Terminology.frequency.desc()).all()
    terms_dict = [t.to_dict() for t in terms]

    if fmt == "json":
        return Response(
            json.dumps({"document_id": doc.id, "document_name": doc.original_filename, "terminology": terms_dict}, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename=terminology_{doc.id[:8]}.json"}
        )

    # Default CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Term", "Normalized Term", "Definition Type", "Definition", "Frequency", "Confidence Score", "Page", "Section", "Source Sentence"])

    for t in terms:
        writer.writerow([
            t.id,
            t.term,
            t.normalized_term,
            t.definition_type,
            t.definition,
            t.frequency,
            round(t.confidence_score, 3),
            t.page_number,
            t.section_heading,
            t.source_sentence
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=terminology_{doc.id[:8]}.csv"}
    )


@export_bp.route("/<document_id>/export/relationships", methods=["GET"])
def export_relationships(document_id):
    """
    GET /api/documents/<document_id>/export/relationships?format=csv|json
    """
    fmt = request.args.get("format", "csv").lower()
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    rels = session.query(Relationship).filter_by(document_id=doc.id).order_by(Relationship.confidence_score.desc()).all()
    rels_dict = [r.to_dict() for r in rels]

    if fmt == "json":
        return Response(
            json.dumps({"document_id": doc.id, "document_name": doc.original_filename, "relationships": rels_dict}, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename=relationships_{doc.id[:8]}.json"}
        )

    # Default CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Source Concept", "Relation Type", "Target Concept", "Confidence Score", "Page", "Section", "Extraction Method", "Supporting Sentence"])

    for r in rels:
        writer.writerow([
            r.id,
            r.source_concept.name if r.source_concept else "Unknown",
            r.relation_type,
            r.target_concept.name if r.target_concept else "Unknown",
            round(r.confidence_score, 3),
            r.source_page,
            r.source_section,
            r.extraction_method,
            r.supporting_sentence
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=relationships_{doc.id[:8]}.csv"}
    )


@export_bp.route("/<document_id>/export/graph", methods=["GET"])
def export_graph_json(document_id):
    """
    GET /api/documents/<document_id>/export/graph
    Exports complete graph topology as JSON.
    """
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    concepts = session.query(Concept).filter_by(document_id=doc.id).all()
    relationships = session.query(Relationship).filter_by(document_id=doc.id).all()

    graph_payload = {
        "metadata": {
            "document_id": doc.id,
            "document_name": doc.original_filename,
            "export_timestamp": doc.upload_date.isoformat() if doc.upload_date else None,
            "total_nodes": len(concepts),
            "total_edges": len(relationships)
        },
        "nodes": [c.to_dict() for c in concepts],
        "edges": [r.to_dict() for r in relationships]
    }

    return Response(
        json.dumps(graph_payload, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename=concept_graph_{doc.id[:8]}.json"}
    )


@export_bp.route("/<document_id>/export/report", methods=["GET"])
def export_pdf_report(document_id):
    """
    GET /api/documents/<document_id>/export/report
    Generates and returns an executive PDF report containing metrics, terminology, and relationship evidence.
    """
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    concepts = session.query(Concept).filter_by(document_id=doc.id).all()
    relationships = session.query(Relationship).filter_by(document_id=doc.id).all()
    terminologies = session.query(Terminology).filter_by(document_id=doc.id).all()

    try:
        pdf_path = PDFReportService.generate_report(
            document_dict=doc.to_dict(),
            concepts=[c.to_dict() for c in concepts],
            relationships=[r.to_dict() for r in relationships],
            terminologies=[t.to_dict() for t in terminologies]
        )
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"report_{doc.id[:8]}.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF report: {str(e)}", "status": 500}), 500
