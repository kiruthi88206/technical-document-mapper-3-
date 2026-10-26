"""
REST API Routes for Technical Document Terminology and Concept Relationship Mapper.
Provides endpoints for document ingestion, NLP processing, graph operations, search, and exports.
"""
import os
import uuid
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from config import Config
from database.db import db_manager
from services.document_extractor import DocumentExtractor
from services.nlp_service import nlp_processor
from graph.relationship_detector import relationship_detector
from graph.graph_builder import KnowledgeGraphBuilder
from services.pdf_generator import PDFReportGenerator

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/status', methods=['GET'])
def get_system_status():
    """Returns database status, active models, and document count."""
    db_status = db_manager.get_status()
    return jsonify({
        "status": "online",
        "system_name": "Technical Document Terminology & Concept Relationship Mapper",
        "database": db_status,
        "spacy_loaded": nlp_processor.spacy_enabled,
        "timestamp": datetime.now().isoformat()
    })


@api_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload PDF, DOCX, or TXT file, validate, and extract raw text and metadata."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        filename = f"document_{uuid.uuid4().hex[:8]}.txt"

    # Read content into memory to check size and validate
    file_bytes = file.read()
    file_size = len(file_bytes)

    valid, reason = DocumentExtractor.validate_file(filename, file_size)
    if not valid:
        return jsonify({"error": reason}), 400

    doc_id = str(uuid.uuid4())
    stored_filename = f"{doc_id}_{filename}"
    file_path = os.path.join(Config.UPLOAD_FOLDER, stored_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    try:
        extracted = DocumentExtractor.extract_text(file_path, filename)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Failed to extract document text: {str(e)}"}), 422

    # Store document record in Database
    doc_record = {
        "_id": doc_id,
        "doc_id": doc_id,
        "filename": filename,
        "stored_filename": stored_filename,
        "file_path": file_path,
        "file_type": extracted["file_type"],
        "file_size": extracted["file_size"],
        "word_count": extracted["word_count"],
        "sentence_count": extracted["sentence_count"],
        "page_count": extracted["page_count"],
        "estimated_reading_time_min": extracted["estimated_reading_time_min"],
        "text": extracted["text"],
        "metadata": extracted["metadata"],
        "status": "uploaded",
        "uploaded_at": datetime.now().isoformat()
    }

    db_manager.documents.insert_one(doc_record)

    return jsonify({
        "message": "Document uploaded and parsed successfully",
        "doc_id": doc_id,
        "filename": filename,
        "file_type": extracted["file_type"],
        "word_count": extracted["word_count"],
        "sentence_count": extracted["sentence_count"],
        "page_count": extracted["page_count"],
        "reading_time_min": extracted["estimated_reading_time_min"]
    }), 201


@api_bp.route('/analyze', methods=['POST'])
def analyze_document():
    """
    Run full NLP and Graph pipeline:
    1. Extract and rank technical terminology
    2. Detect inter-concept relationships
    3. Construct and format knowledge graph
    4. Store results in Database
    """
    data = request.get_json(silent=True) or {}
    doc_id = data.get("doc_id")
    raw_text = data.get("text")
    doc_title = data.get("title", "Technical Document")

    # If analyzing an existing uploaded document
    doc_record = None
    if doc_id:
        doc_record = db_manager.documents.find_one({"doc_id": doc_id}) or db_manager.documents.find_one({"_id": doc_id})
        if not doc_record:
            return jsonify({"error": f"Document with ID '{doc_id}' not found."}), 404
        raw_text = doc_record.get("text", "")
        doc_title = doc_record.get("filename", doc_title)
    elif raw_text:
        # Create a transient document entry for direct text input
        doc_id = str(uuid.uuid4())
        doc_record = {
            "_id": doc_id,
            "doc_id": doc_id,
            "filename": doc_title,
            "file_type": "TEXT",
            "file_size": len(raw_text.encode('utf-8')),
            "word_count": len(raw_text.split()),
            "sentence_count": len(raw_text.split(".")),
            "page_count": 1,
            "text": raw_text,
            "status": "uploaded",
            "uploaded_at": datetime.now().isoformat()
        }
        db_manager.documents.insert_one(doc_record)
    else:
        return jsonify({"error": "Either 'doc_id' or 'text' must be provided."}), 400

    if not raw_text or len(raw_text.strip()) < 20:
        return jsonify({"error": "Document content is too brief to extract meaningful technical concepts."}), 422

    max_concepts = int(data.get("max_concepts", Config.MAX_CONCEPTS_DEFAULT))

    try:
        # 1. Terminology Extraction & Ranking
        nlp_results = nlp_processor.process_document(raw_text, max_concepts=max_concepts)
        concepts = nlp_results["concepts"]
        glossary = nlp_results["glossary"]
        sentences = nlp_results["sentences"]

        if not concepts:
            return jsonify({"error": "No technical terminology could be extracted from this text."}), 422

        # 2. Relationship Detection
        relationships = relationship_detector.detect_relationships(concepts, sentences, document_title=doc_title)

        # 3. Knowledge Graph Construction
        graph_data = KnowledgeGraphBuilder.build_graph(concepts, relationships)

        # 4. Associate and Store in Database
        # Clean previous analysis records for this document if any
        db_manager.concepts.delete_many({"doc_id": doc_id})
        db_manager.relationships.delete_many({"doc_id": doc_id})
        db_manager.glossary.delete_many({"doc_id": doc_id})

        for c in concepts:
            c_doc = dict(c)
            c_doc["doc_id"] = doc_id
            db_manager.concepts.insert_one(c_doc)

        for r in relationships:
            r_doc = dict(r)
            r_doc["doc_id"] = doc_id
            db_manager.relationships.insert_one(r_doc)

        for g in glossary:
            g_doc = dict(g)
            g_doc["doc_id"] = doc_id
            db_manager.glossary.insert_one(g_doc)

        # Save analysis summary
        analysis_record = {
            "doc_id": doc_id,
            "analyzed_at": datetime.now().isoformat(),
            "concept_count": len(concepts),
            "relationship_count": len(relationships),
            "graph_metrics": graph_data["metrics"],
            "nodes": graph_data["nodes"],
            "edges": graph_data["edges"]
        }
        db_manager.analysis_results.delete_many({"doc_id": doc_id})
        db_manager.analysis_results.insert_one(analysis_record)

        # Update document status
        db_manager.documents.update_one({"doc_id": doc_id}, {"$set": {"status": "analyzed", "analyzed_at": datetime.now().isoformat()}})

        return jsonify({
            "message": "Document analyzed and knowledge graph generated successfully",
            "doc_id": doc_id,
            "document_title": doc_title,
            "concepts_count": len(concepts),
            "relationships_count": len(relationships),
            "graph": graph_data,
            "glossary": glossary,
            "metrics": graph_data["metrics"]
        })

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@api_bp.route('/documents', methods=['GET'])
def list_documents():
    """List all stored documents and their analysis status."""
    docs = db_manager.documents.find()
    summary_list = []
    for d in docs:
        doc_id = d.get("doc_id") or d.get("_id")
        concept_count = db_manager.concepts.count_documents({"doc_id": doc_id})
        rel_count = db_manager.relationships.count_documents({"doc_id": doc_id})
        summary_list.append({
            "doc_id": doc_id,
            "filename": d.get("filename", "Untitled"),
            "file_type": d.get("file_type", "TXT"),
            "file_size": d.get("file_size", 0),
            "word_count": d.get("word_count", 0),
            "sentence_count": d.get("sentence_count", 0),
            "status": d.get("status", "uploaded"),
            "uploaded_at": d.get("uploaded_at", ""),
            "concept_count": concept_count,
            "relationship_count": rel_count
        })
    summary_list.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return jsonify({"documents": summary_list, "total": len(summary_list)})


@api_bp.route('/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """Retrieve metadata and details for a specific document."""
    doc = db_manager.documents.find_one({"doc_id": doc_id}) or db_manager.documents.find_one({"_id": doc_id})
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    # Sanitize text for transfer
    safe_doc = dict(doc)
    safe_doc["text_preview"] = doc.get("text", "")[:1200]
    if "text" in safe_doc:
        del safe_doc["text"]

    return jsonify(safe_doc)


@api_bp.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete document and all associated concepts, relations, and analysis."""
    doc = db_manager.documents.find_one({"doc_id": doc_id}) or db_manager.documents.find_one({"_id": doc_id})
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    # Remove file on disk if exists
    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    db_manager.documents.delete_one({"doc_id": doc_id})
    db_manager.documents.delete_one({"_id": doc_id})
    db_manager.concepts.delete_many({"doc_id": doc_id})
    db_manager.relationships.delete_many({"doc_id": doc_id})
    db_manager.glossary.delete_many({"doc_id": doc_id})
    db_manager.analysis_results.delete_many({"doc_id": doc_id})
    db_manager.graph_edits.delete_many({"doc_id": doc_id})

    return jsonify({"message": f"Document {doc_id} and all related data deleted successfully"})


@api_bp.route('/graph/<doc_id>', methods=['GET'])
def get_graph(doc_id):
    """Get active nodes and edges for the document, including any user edits."""
    analysis = db_manager.analysis_results.find_one({"doc_id": doc_id})
    if not analysis:
        # Check if concepts exist, build on demand
        concepts = db_manager.concepts.find({"doc_id": doc_id})
        rels = db_manager.relationships.find({"doc_id": doc_id})
        if not concepts:
            return jsonify({"error": "No analysis found for this document. Please run /api/analyze first."}), 404
        graph_data = KnowledgeGraphBuilder.build_graph(concepts, rels)
    else:
        graph_data = {
            "nodes": analysis.get("nodes", []),
            "edges": analysis.get("edges", []),
            "metrics": analysis.get("graph_metrics", {})
        }

    # Check for any user edits / overrides
    edits = db_manager.graph_edits.find_one({"doc_id": doc_id})
    if edits:
        graph_data["nodes"] = edits.get("nodes", graph_data["nodes"])
        graph_data["edges"] = edits.get("edges", graph_data["edges"])
        graph_data["is_customized"] = True
    else:
        graph_data["is_customized"] = False

    return jsonify(graph_data)


@api_bp.route('/glossary/<doc_id>', methods=['GET'])
def get_glossary(doc_id):
    """Retrieve auto-generated glossary entries for a document."""
    entries = db_manager.glossary.find({"doc_id": doc_id})
    if not entries:
        # Fallback to concepts
        concepts = db_manager.concepts.find({"doc_id": doc_id})
        entries = [{
            "term": c["name"],
            "category": c.get("category", "Core Concepts"),
            "frequency": c.get("frequency", 1),
            "definition": c.get("definition", ""),
            "origin": c.get("origin", "Document Context"),
            "context_sentence": c.get("context_sentence", "")
        } for c in concepts]

    return jsonify({"glossary": entries, "count": len(entries)})


@api_bp.route('/search', methods=['GET'])
def search_concepts():
    """Search concepts across documents or within a specific document."""
    query = request.args.get('q', '').strip().lower()
    doc_id = request.args.get('doc_id')

    if not query:
        return jsonify({"results": []})

    filter_dict = {}
    if doc_id:
        filter_dict["doc_id"] = doc_id

    concepts = db_manager.concepts.find(filter_dict)
    matched = []

    for c in concepts:
        name = c.get("name", "").lower()
        definition = c.get("definition", "").lower()
        category = c.get("category", "").lower()

        if query in name or query in definition or query in category:
            matched.append({
                "concept_id": c.get("concept_id") or c.get("id"),
                "name": c.get("name"),
                "category": c.get("category"),
                "frequency": c.get("frequency", 1),
                "definition": c.get("definition", ""),
                "doc_id": c.get("doc_id")
            })

    return jsonify({"results": matched, "query": query, "total": len(matched)})


# Graph Editing Endpoints (Add Node, Edit Node, Delete Node, Add Edge, Reset)
@api_bp.route('/graph/<doc_id>/node', methods=['POST'])
def add_graph_node(doc_id):
    """Allow user to manually add a new concept node to the knowledge graph."""
    data = request.get_json() or {}
    label = data.get("label", "").strip()
    category = data.get("category", "Core Concepts")
    definition = data.get("definition", f"User-created concept: {label}")

    if not label:
        return jsonify({"error": "Node label is required"}), 400

    # Get current graph
    current_graph = _get_active_graph(doc_id)
    new_node_id = f"custom_{uuid.uuid4().hex[:6]}"

    from graph.graph_builder import CATEGORY_COLORS, DEFAULT_COLOR
    color_scheme = CATEGORY_COLORS.get(category, DEFAULT_COLOR)

    new_node = {
        "id": new_node_id,
        "label": label,
        "category": category,
        "value": 30,
        "title": f"<div style='padding:4px;'><b>{label}</b><br/>{category}<br/>{definition}</div>",
        "color": {
            "background": color_scheme["background"],
            "border": color_scheme["border"],
            "highlight": color_scheme["highlight"]
        },
        "font": {"color": "#F8FAFC", "size": 13, "face": "Inter, system-ui"},
        "shape": "dot",
        "frequency": 1,
        "definition": definition,
        "is_custom": True
    }

    current_graph["nodes"].append(new_node)
    _save_active_graph(doc_id, current_graph)

    return jsonify({"message": "Node added successfully", "node": new_node})


@api_bp.route('/graph/<doc_id>/node/<node_id>', methods=['PUT'])
def edit_graph_node(doc_id, node_id):
    """Edit an existing node label or category."""
    data = request.get_json() or {}
    new_label = data.get("label", "").strip()
    new_category = data.get("category")

    current_graph = _get_active_graph(doc_id)
    found = False
    for n in current_graph["nodes"]:
        if str(n["id"]) == str(node_id):
            if new_label:
                n["label"] = new_label
            if new_category:
                n["category"] = new_category
                from graph.graph_builder import CATEGORY_COLORS, DEFAULT_COLOR
                color_scheme = CATEGORY_COLORS.get(new_category, DEFAULT_COLOR)
                n["color"] = {
                    "background": color_scheme["background"],
                    "border": color_scheme["border"],
                    "highlight": color_scheme["highlight"]
                }
            found = True
            break

    if not found:
        return jsonify({"error": "Node not found"}), 404

    _save_active_graph(doc_id, current_graph)
    return jsonify({"message": "Node updated successfully"})


@api_bp.route('/graph/<doc_id>/node/<node_id>', methods=['DELETE'])
def delete_graph_node(doc_id, node_id):
    """Delete a node and its attached edges from the graph."""
    current_graph = _get_active_graph(doc_id)
    initial_nodes = len(current_graph["nodes"])
    current_graph["nodes"] = [n for n in current_graph["nodes"] if str(n["id"]) != str(node_id)]

    if len(current_graph["nodes"]) == initial_nodes:
        return jsonify({"error": "Node not found"}), 404

    # Remove attached edges
    current_graph["edges"] = [e for e in current_graph["edges"] if str(e.get("from")) != str(node_id) and str(e.get("to")) != str(node_id)]
    _save_active_graph(doc_id, current_graph)

    return jsonify({"message": f"Node {node_id} and connected edges removed"})


@api_bp.route('/graph/<doc_id>/edge', methods=['POST'])
def add_graph_edge(doc_id):
    """Add a new relationship edge between two nodes."""
    data = request.get_json() or {}
    src = str(data.get("from", "")).strip()
    dst = str(data.get("to", "")).strip()
    label = data.get("label", "related_to").strip()

    if not src or not dst:
        return jsonify({"error": "Source and target node IDs are required"}), 400

    current_graph = _get_active_graph(doc_id)
    new_edge_id = f"custom_e_{uuid.uuid4().hex[:6]}"

    new_edge = {
        "id": new_edge_id,
        "from": src,
        "to": dst,
        "label": label.replace("_", " "),
        "arrows": {"to": {"enabled": True, "scaleFactor": 0.8}},
        "width": 2.2,
        "color": {"color": "#818CF8", "highlight": "#38BDF8"},
        "font": {"color": "#94A3B8", "size": 10, "strokeWidth": 2, "strokeColor": "#0F172A"},
        "confidence": 0.85,
        "relation_type": label,
        "is_custom": True
    }

    current_graph["edges"].append(new_edge)
    _save_active_graph(doc_id, current_graph)

    return jsonify({"message": "Edge added successfully", "edge": new_edge})


@api_bp.route('/graph/<doc_id>/edge/<edge_id>', methods=['DELETE'])
def delete_graph_edge(doc_id, edge_id):
    """Delete an edge from the graph."""
    current_graph = _get_active_graph(doc_id)
    initial_edges = len(current_graph["edges"])
    current_graph["edges"] = [e for e in current_graph["edges"] if str(e.get("id")) != str(edge_id)]

    if len(current_graph["edges"]) == initial_edges:
        return jsonify({"error": "Edge not found"}), 404

    _save_active_graph(doc_id, current_graph)
    return jsonify({"message": f"Edge {edge_id} removed"})


@api_bp.route('/graph/<doc_id>/reset', methods=['POST'])
def reset_graph(doc_id):
    """Reset graph back to the original algorithmically extracted state."""
    db_manager.graph_edits.delete_many({"doc_id": doc_id})
    analysis = db_manager.analysis_results.find_one({"doc_id": doc_id})
    if not analysis:
        return jsonify({"error": "Original analysis not found"}), 404

    return jsonify({
        "message": "Graph reset to original extracted state",
        "nodes": analysis.get("nodes", []),
        "edges": analysis.get("edges", [])
    })


# Export Endpoints (JSON, CSV, PDF)
@api_bp.route('/export/<doc_id>', methods=['GET'])
def export_data(doc_id):
    """Export analysis data as JSON, CSV, or PDF."""
    fmt = request.args.get('format', 'json').lower()
    doc = db_manager.documents.find_one({"doc_id": doc_id}) or db_manager.documents.find_one({"_id": doc_id})
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    concepts = db_manager.concepts.find({"doc_id": doc_id})
    relationships = db_manager.relationships.find({"doc_id": doc_id})
    glossary = db_manager.glossary.find({"doc_id": doc_id})
    graph_data = _get_active_graph(doc_id)

    if fmt == 'json':
        export_payload = {
            "document": {
                "id": doc_id,
                "filename": doc.get("filename"),
                "file_type": doc.get("file_type"),
                "word_count": doc.get("word_count"),
                "sentence_count": doc.get("sentence_count"),
                "uploaded_at": doc.get("uploaded_at")
            },
            "concepts": concepts,
            "relationships": relationships,
            "glossary": glossary,
            "graph": graph_data
        }
        return jsonify(export_payload)

    elif fmt == 'csv':
        # Export Glossary as CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Term", "Category", "Frequency", "Definition", "Origin", "Context Excerpt"])
        for g in glossary:
            writer.writerow([
                g.get("term", ""),
                g.get("category", ""),
                g.get("frequency", 1),
                g.get("definition", ""),
                g.get("origin", ""),
                g.get("context_sentence", "")
            ])
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{secure_filename(doc.get('filename', 'document'))}_glossary.csv"
        )

    elif fmt == 'pdf':
        output_filename = f"report_{doc_id[:8]}.pdf"
        try:
            pdf_path = PDFReportGenerator.generate_report(
                document_meta=doc,
                concepts=concepts,
                relationships=relationships,
                glossary=glossary,
                graph_metrics=graph_data.get("metrics", {}),
                output_filename=output_filename
            )
            return send_file(
                pdf_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"Report_{secure_filename(doc.get('filename', 'document'))}.pdf"
            )
        except Exception as e:
            return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500

    else:
        return jsonify({"error": f"Unsupported format '{fmt}'. Choose 'json', 'csv', or 'pdf'."}), 400


# Sample Document Loader for Instant Demo
@api_bp.route('/sample/<sample_id>', methods=['POST'])
def load_sample_document(sample_id):
    """Load a pre-configured sample technical document for instant evaluation and demo."""
    sample_files = {
        "nlp_architecture": ("deep_learning_nlp_architecture.txt", "Deep Learning & NLP Architecture Overview"),
        "microservices": ("distributed_systems_microservices.txt", "Cloud Microservices & Distributed Architecture")
    }

    if sample_id not in sample_files:
        return jsonify({"error": f"Unknown sample '{sample_id}'. Available: {list(sample_files.keys())}"}), 404

    filename, title = sample_files[sample_id]
    sample_path = os.path.join(Config.SAMPLE_FOLDER, filename)

    if not os.path.exists(sample_path):
        return jsonify({"error": f"Sample file '{filename}' not found."}), 404

    with open(sample_path, "r", encoding="utf-8") as f:
        text = f.read()

    doc_id = str(uuid.uuid4())
    extracted = DocumentExtractor.extract_text(sample_path, filename)

    doc_record = {
        "_id": doc_id,
        "doc_id": doc_id,
        "filename": filename,
        "stored_filename": f"sample_{filename}",
        "file_path": sample_path,
        "file_type": "TXT",
        "file_size": len(text.encode('utf-8')),
        "word_count": extracted["word_count"],
        "sentence_count": extracted["sentence_count"],
        "page_count": 1,
        "estimated_reading_time_min": extracted["estimated_reading_time_min"],
        "text": text,
        "metadata": {"source": "Pre-loaded Sample Document", "title": title},
        "status": "uploaded",
        "uploaded_at": datetime.now().isoformat()
    }
    db_manager.documents.insert_one(doc_record)

    return jsonify({
        "message": f"Sample document '{title}' loaded successfully",
        "doc_id": doc_id,
        "filename": filename,
        "title": title,
        "word_count": extracted["word_count"],
        "sentence_count": extracted["sentence_count"]
    }), 201


# Helper Functions
def _get_active_graph(doc_id: str) -> Dict[str, Any]:
    """Retrieve active graph data with any user-customized modifications."""
    edits = db_manager.graph_edits.find_one({"doc_id": doc_id})
    if edits:
        return {
            "nodes": edits.get("nodes", []),
            "edges": edits.get("edges", []),
            "metrics": edits.get("metrics", {})
        }

    analysis = db_manager.analysis_results.find_one({"doc_id": doc_id})
    if analysis:
        return {
            "nodes": analysis.get("nodes", []),
            "edges": analysis.get("edges", []),
            "metrics": analysis.get("graph_metrics", {})
        }

    # Reconstruct from concepts and relations
    concepts = db_manager.concepts.find({"doc_id": doc_id})
    rels = db_manager.relationships.find({"doc_id": doc_id})
    return KnowledgeGraphBuilder.build_graph(concepts, rels)


def _save_active_graph(doc_id: str, graph_data: Dict[str, Any]):
    """Save user modifications to graph_edits collection."""
    db_manager.graph_edits.update_one(
        {"doc_id": doc_id},
        {"$set": {
            "doc_id": doc_id,
            "nodes": graph_data.get("nodes", []),
            "edges": graph_data.get("edges", []),
            "updated_at": datetime.now().isoformat()
        }}
    ) or db_manager.graph_edits.insert_one({
        "doc_id": doc_id,
        "nodes": graph_data.get("nodes", []),
        "edges": graph_data.get("edges", []),
        "updated_at": datetime.now().isoformat()
    })
