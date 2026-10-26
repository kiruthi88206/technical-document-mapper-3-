import os
import uuid
from flask import Blueprint, request, jsonify
from ..database import get_db
from ..models import Document, DocumentChunk, ProcessingJob
from ..services.document_extractor import DocumentExtractor
from ..processors.nlp_processor import DocumentNLPProcessor

document_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

@document_bp.route("/upload", methods=["POST"])
def upload_document():
    """
    POST /api/documents/upload
    Validates file extension and size, saves file safely with a UUID name,
    extracts chunks with page numbers and offsets, creates Document and DocumentChunk records.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request.", "status": 400}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected for upload.", "status": 400}), 400

    file_bytes = file.read()
    is_valid, err_msg, detected_ext = DocumentExtractor.validate_upload(file.filename, file_bytes)
    if not is_valid:
        return jsonify({"error": err_msg, "status": 400}), 400

    # Save safely
    try:
        stored_filename, saved_path = DocumentExtractor.save_uploaded_file(file.filename, file_bytes)
    except Exception as e:
        return jsonify({"error": f"Failed to store uploaded file: {str(e)}", "status": 500}), 500

    # Extract text and chunks
    try:
        extracted_data = DocumentExtractor.extract_document(saved_path, detected_ext)
    except Exception as e:
        # Clean up saved file if extraction fails
        if os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except Exception:
                pass
        return jsonify({"error": f"Extraction error: {str(e)}", "status": 422}), 422

    session = get_db()
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_type=detected_ext,
        file_size=len(file_bytes),
        storage_path=saved_path,
        status="uploaded",
        warning_message=extracted_data.get("warning_message", ""),
        total_chunks=len(extracted_data["chunks"]),
        word_count=extracted_data["word_count"],
        sentence_count=extracted_data["sentence_count"]
    )
    session.add(doc)

    for chk in extracted_data["chunks"]:
        chunk_obj = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            chunk_index=chk["chunk_index"],
            section_heading=chk["section_heading"],
            page_number=chk["page_number"],
            start_offset=chk["start_offset"],
            end_offset=chk["end_offset"],
            text=chk["text"],
            token_count=chk["token_count"]
        )
        session.add(chunk_obj)

    # Initial Processing Job
    job = ProcessingJob(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        status="uploaded",
        progress_percent=0,
        current_stage="ready",
        stage_message="File ingested and segmented. Ready for NLP analysis."
    )
    session.add(job)
    session.commit()

    return jsonify({
        "success": True,
        "message": "Document uploaded and parsed successfully.",
        "document": doc.to_dict()
    }), 201


@document_bp.route("", methods=["GET"])
def list_documents():
    """
    GET /api/documents
    List all uploaded documents with real database statistics and pagination.
    """
    session = get_db()
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)

    query = session.query(Document).order_by(Document.upload_date.desc())
    total = query.count()
    docs = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "success": True,
        "total": total,
        "page": page,
        "limit": limit,
        "documents": [d.to_dict() for d in docs]
    })


@document_bp.route("/<document_id>", methods=["GET"])
def get_document(document_id):
    """
    GET /api/documents/<document_id>
    Retrieve document detail, including preview of chunks and status.
    """
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    chunks = session.query(DocumentChunk).filter_by(document_id=doc.id).order_by(DocumentChunk.chunk_index).all()
    latest_job = session.query(ProcessingJob).filter_by(document_id=doc.id).order_by(ProcessingJob.created_at.desc()).first()

    result = doc.to_dict()
    result["chunks_preview"] = [c.to_dict() for c in chunks[:10]]
    result["latest_job"] = latest_job.to_dict() if latest_job else None

    return jsonify({"success": True, "document": result})


@document_bp.route("/<document_id>", methods=["DELETE"])
def delete_document(document_id):
    """
    DELETE /api/documents/<document_id>
    Deletes document and cascades all chunks, terms, concepts, relationships, and files.
    """
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    # Remove storage file if it exists
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception:
            pass

    session.delete(doc)
    session.commit()

    return jsonify({"success": True, "message": f"Document '{document_id}' deleted successfully."})


@document_bp.route("/<document_id>/process", methods=["POST"])
def process_document(document_id):
    """
    POST /api/documents/<document_id>/process
    Triggers the end-to-end NLP processing pipeline.
    """
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    data = request.get_json(silent=True) or {}
    max_terms = data.get("max_terms", 40)
    min_freq = data.get("min_term_freq", 1)

    try:
        res = DocumentNLPProcessor.process_document(
            document_id=document_id,
            max_terms=max_terms,
            min_freq=min_freq
        )
        return jsonify({
            "success": True,
            "message": "Document processed successfully.",
            "data": res
        })
    except Exception as e:
        return jsonify({"error": f"Processing failure: {str(e)}", "status": 500}), 500


@document_bp.route("/<document_id>/status", methods=["GET"])
def get_processing_status(document_id):
    """
    GET /api/documents/<document_id>/status
    Returns the current processing status and job progress.
    """
    session = get_db()
    doc = session.query(Document).filter_by(id=document_id).first()
    if not doc:
        return jsonify({"error": f"Document '{document_id}' not found.", "status": 404}), 404

    latest_job = session.query(ProcessingJob).filter_by(document_id=doc.id).order_by(ProcessingJob.created_at.desc()).first()

    return jsonify({
        "success": True,
        "document_id": doc.id,
        "status": doc.status,
        "error_message": doc.error_message,
        "warning_message": doc.warning_message,
        "job": latest_job.to_dict() if latest_job else None
    })
