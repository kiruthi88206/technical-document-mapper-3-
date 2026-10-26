import uuid
from models.concept_model import ConceptModel
from models.relationship_model import RelationshipModel
from database.mongodb import db_manager

class GraphService:
    @staticmethod
    def get_graph_data(doc_id):
        """Format concepts and relationships into Cytoscape.js compatible elements."""
        concepts = list(ConceptModel.get_by_document(doc_id))
        relationships = list(RelationshipModel.get_by_document(doc_id))

        nodes = []
        for c in concepts:
            # Map score to visual node size (min 30px, max 75px)
            score = float(c.get('relevance_score', 0.5))
            node_size = int(30 + score * 45)
            
            nodes.append({
                'data': {
                    'id': c['_id'],
                    'label': c['name'],
                    'name': c['name'],
                    'frequency': c.get('frequency', 1),
                    'relevance_score': score,
                    'category': c.get('category', 'Core Concept'),
                    'definition': c.get('definition', ''),
                    'node_size': node_size,
                    'pos_tag': c.get('pos_tag', 'NNP')
                }
            })

        # Name to ID mapping for edges
        name_to_id = {c['name']: c['_id'] for c in concepts}
        
        edges = []
        for r in relationships:
            src_name = r['source']
            tgt_name = r['target']
            
            src_id = name_to_id.get(src_name, src_name)
            tgt_id = name_to_id.get(tgt_name, tgt_name)
            
            strength = float(r.get('strength', 0.5))
            # Map strength to edge width (min 1.5px, max 8px)
            line_width = round(1.5 + strength * 6.5, 1)
            
            edges.append({
                'data': {
                    'id': r['_id'],
                    'source': src_id,
                    'target': tgt_id,
                    'source_name': src_name,
                    'target_name': tgt_name,
                    'relationship_type': r.get('relationship_type', 'semantic_similarity'),
                    'strength': strength,
                    'line_width': line_width,
                    'reason': r.get('reason', 'Semantic similarity')
                }
            })

        return {
            'document_id': doc_id,
            'elements': {
                'nodes': nodes,
                'edges': edges
            },
            'stats': {
                'nodes_count': len(nodes),
                'edges_count': len(edges)
            }
        }

    @staticmethod
    def add_node(doc_id, name, category="User Defined", definition="", relevance_score=0.8, frequency=1):
        concept_data = {
            '_id': str(uuid.uuid4()),
            'document_id': doc_id,
            'name': name,
            'category': category,
            'definition': definition or f"{name} added manually.",
            'relevance_score': float(relevance_score),
            'frequency': int(frequency),
            'pos_tag': 'NNP'
        }
        ConceptModel.create_many([concept_data])
        
        # Also add to glossary
        db_manager.get_collection('glossary').insert_one({
            '_id': str(uuid.uuid4()),
            'document_id': doc_id,
            'term': name,
            'definition': concept_data['definition'],
            'frequency': concept_data['frequency'],
            'relevance_score': concept_data['relevance_score'],
            'category': category,
            'related_concepts': []
        })
        return concept_data

    @staticmethod
    def add_edge(doc_id, source_name, target_name, relationship_type="manual_link", strength=0.85, reason="User added relationship"):
        rel_data = {
            '_id': str(uuid.uuid4()),
            'document_id': doc_id,
            'source': source_name,
            'target': target_name,
            'relationship_type': relationship_type,
            'strength': float(strength),
            'reason': reason
        }
        RelationshipModel.create_many([rel_data])
        return rel_data

    @staticmethod
    def delete_node(node_id):
        return ConceptModel.delete(node_id)

    @staticmethod
    def delete_edge(edge_id):
        return RelationshipModel.delete(edge_id)

    @staticmethod
    def update_node(node_id, name, definition=None, relevance_score=None, category=None):
        update_data = {}
        if name: update_data['name'] = name
        if definition: update_data['definition'] = definition
        if relevance_score is not None: update_data['relevance_score'] = float(relevance_score)
        if category: update_data['category'] = category
        
        ConceptModel.update(node_id, update_data)
        concept = ConceptModel.get_by_id(node_id)
        if concept and name:
            # Update glossary entry
            db_manager.get_collection('glossary').update_one(
                {'document_id': concept.get('document_id'), 'term': concept.get('name')},
                {'$set': {'term': name, 'definition': concept.get('definition', '')}}
            )
        return concept

    @staticmethod
    def update_edge(edge_id, strength=None, relationship_type=None, reason=None):
        update_data = {}
        if strength is not None: update_data['strength'] = float(strength)
        if relationship_type: update_data['relationship_type'] = relationship_type
        if reason: update_data['reason'] = reason
        
        return RelationshipModel.update(edge_id, update_data)
