from flask import Blueprint, request, jsonify
from database.mongodb import db_manager
from models.document_model import DocumentModel

glossary_bp = Blueprint('glossary_bp', __name__)

@glossary_bp.route('/api/glossary/<doc_id>', methods=['GET'])
def get_glossary(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    sort_by = request.args.get('sort', 'alphabetical')
    search_q = request.args.get('search', '').strip().lower()

    coll = db_manager.get_collection('glossary')
    items = list(coll.find({'document_id': doc_id}))

    # Filter search if query provided
    if search_q:
        items = [
            item for item in items 
            if search_q in item.get('term', '').lower() or search_q in item.get('definition', '').lower()
        ]

    # Sorting
    if sort_by == 'importance':
        items.sort(key=lambda x: float(x.get('relevance_score', 0)), reverse=True)
    elif sort_by == 'frequency':
        items.sort(key=lambda x: int(x.get('frequency', 0)), reverse=True)
    else:  # alphabetical
        items.sort(key=lambda x: x.get('term', '').lower())

    return jsonify({
        'document_id': doc_id,
        'count': len(items),
        'glossary': items
    }), 200
