from flask import Blueprint, request, jsonify
from services.graph_service import GraphService
from models.document_model import DocumentModel

graph_bp = Blueprint('graph_bp', __name__)

@graph_bp.route('/api/graph/<doc_id>', methods=['GET'])
def get_graph(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
        
    graph_data = GraphService.get_graph_data(doc_id)
    return jsonify(graph_data), 200


@graph_bp.route('/api/graph/node', methods=['POST'])
def add_node():
    data = request.get_json() or {}
    doc_id = data.get('document_id')
    name = data.get('name')
    
    if not doc_id or not name:
        return jsonify({'error': 'document_id and node name are required.'}), 400
        
    node = GraphService.add_node(
        doc_id=doc_id,
        name=name,
        category=data.get('category', 'Custom Concept'),
        definition=data.get('definition', ''),
        relevance_score=data.get('relevance_score', 0.8),
        frequency=data.get('frequency', 1)
    )
    return jsonify({'message': 'Node added successfully', 'node': node}), 201


@graph_bp.route('/api/graph/edge', methods=['POST'])
def add_edge():
    data = request.get_json() or {}
    doc_id = data.get('document_id')
    source = data.get('source')
    target = data.get('target')
    
    if not doc_id or not source or not target:
        return jsonify({'error': 'document_id, source, and target are required.'}), 400
        
    edge = GraphService.add_edge(
        doc_id=doc_id,
        source_name=source,
        target_name=target,
        relationship_type=data.get('relationship_type', 'custom_link'),
        strength=data.get('strength', 0.85),
        reason=data.get('reason', 'User established relationship')
    )
    return jsonify({'message': 'Edge added successfully', 'edge': edge}), 201


@graph_bp.route('/api/graph/node/<node_id>', methods=['PUT'])
def update_node(node_id):
    data = request.get_json() or {}
    updated = GraphService.update_node(
        node_id=node_id,
        name=data.get('name'),
        definition=data.get('definition'),
        relevance_score=data.get('relevance_score'),
        category=data.get('category')
    )
    return jsonify({'message': 'Node updated successfully', 'node': updated}), 200


@graph_bp.route('/api/graph/edge/<edge_id>', methods=['PUT'])
def update_edge(edge_id):
    data = request.get_json() or {}
    updated = GraphService.update_edge(
        edge_id=edge_id,
        strength=data.get('strength'),
        relationship_type=data.get('relationship_type'),
        reason=data.get('reason')
    )
    return jsonify({'message': 'Relationship updated successfully'}), 200


@graph_bp.route('/api/graph/node/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    GraphService.delete_node(node_id)
    return jsonify({'message': 'Node deleted successfully'}), 200


@graph_bp.route('/api/graph/edge/<edge_id>', methods=['DELETE'])
def delete_edge(edge_id):
    GraphService.delete_edge(edge_id)
    return jsonify({'message': 'Edge deleted successfully'}), 200


@graph_bp.route('/api/export/<doc_id>', methods=['GET'])
def export_graph(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
        
    graph_data = GraphService.get_graph_data(doc_id)
    export_payload = {
        'document_metadata': doc,
        'knowledge_graph': graph_data['elements'],
        'statistics': graph_data['stats']
    }
    return jsonify(export_payload), 200
