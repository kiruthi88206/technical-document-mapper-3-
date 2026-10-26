import re
from flask import Blueprint, request, jsonify
from database.mongodb import db_manager
from models.document_model import DocumentModel

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/api/search', methods=['GET'])
def search_concepts():
    query = request.args.get('q', '').strip()
    doc_id = request.args.get('doc_id', '').strip()

    if not query:
        return jsonify({'error': 'Search query parameters missing'}), 400

    # If no doc_id supplied, pick latest analyzed document
    if not doc_id:
        docs = list(DocumentModel.get_all())
        analyzed_docs = [d for d in docs if d.get('status') == 'analyzed']
        if analyzed_docs:
            analyzed_docs.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            doc_id = analyzed_docs[0]['_id']
        elif docs:
            doc_id = docs[0]['_id']
        else:
            return jsonify({'error': 'No document uploaded yet. Please upload a document first.'}), 404

    # Extract target term from query (e.g. "What is NLP?" -> "NLP")
    cleaned_term = _extract_target_term(query)
    
    concepts_coll = db_manager.get_collection('concepts')
    all_concepts = list(concepts_coll.find({'document_id': doc_id}))
    
    relationships_coll = db_manager.get_collection('relationships')
    all_rels = list(relationships_coll.find({'document_id': doc_id}))

    matches = []
    
    # 1. Exact or Substring match
    for c in all_concepts:
        name = c['name']
        def_text = c.get('definition', '')
        
        # Check string match
        if (cleaned_term.lower() in name.lower() or 
            name.lower() in cleaned_term.lower() or 
            any(w.lower() in name.lower() for w in cleaned_term.split() if len(w) > 3)):
            
            # Find related concepts
            related = []
            for r in all_rels:
                if r['source'].lower() == name.lower():
                    related.append({'name': r['target'], 'strength': r.get('strength', 0.5)})
                elif r['target'].lower() == name.lower():
                    related.append({'name': r['source'], 'strength': r.get('strength', 0.5)})
            
            related.sort(key=lambda x: x['strength'], reverse=True)
            
            matches.append({
                'concept_id': c['_id'],
                'name': c['name'],
                'definition': def_text,
                'frequency': c.get('frequency', 1),
                'relevance_score': c.get('relevance_score', 0.5),
                'category': c.get('category', 'Core Concept'),
                'related_concepts': [r['name'] for r in related[:6]],
                'match_type': 'Direct Concept Match'
            })

    # Sort matches by relevance score
    matches.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Save to search history
    db_manager.get_collection('search_history').insert_one({
        'query': query,
        'doc_id': doc_id,
        'results_count': len(matches)
    })

    return jsonify({
        'query': query,
        'document_id': doc_id,
        'count': len(matches),
        'results': matches
    }), 200


def _extract_target_term(query):
    """Extract key subject from natural language question."""
    q = re.sub(r'[^\w\s]', '', query)
    # Strip common question prefixes
    prefixes = [
        'what is', 'what are', 'define', 'explain', 'show concepts related to',
        'what concepts are related to', 'tell me about', 'search', 'find'
    ]
    q_lower = q.lower()
    for prefix in prefixes:
        if q_lower.startswith(prefix):
            q = q[len(prefix):].strip()
            break
    return q if q else query
