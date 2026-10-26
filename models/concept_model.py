import uuid
from database.mongodb import db_manager

class ConceptModel:
    @staticmethod
    def create_many(concepts_list):
        if not concepts_list:
            return []
        coll = db_manager.get_collection('concepts')
        inserted = []
        for item in concepts_list:
            if '_id' not in item:
                item['_id'] = str(uuid.uuid4())
            coll.insert_one(item)
            inserted.append(item)
        return inserted

    @staticmethod
    def get_by_document(doc_id):
        coll = db_manager.get_collection('concepts')
        return coll.find({'document_id': doc_id})

    @staticmethod
    def get_by_id(concept_id):
        coll = db_manager.get_collection('concepts')
        return coll.find_one({'_id': concept_id})

    @staticmethod
    def update(concept_id, update_data):
        coll = db_manager.get_collection('concepts')
        return coll.update_one({'_id': concept_id}, {'$set': update_data})

    @staticmethod
    def delete(concept_id):
        coll = db_manager.get_collection('concepts')
        concept = coll.find_one({'_id': concept_id})
        if concept:
            doc_id = concept.get('document_id')
            name = concept.get('name')
            # Delete connected relationships
            rel_coll = db_manager.get_collection('relationships')
            rel_coll.delete_many({'document_id': doc_id, 'source': name})
            rel_coll.delete_many({'document_id': doc_id, 'target': name})
            # Delete glossary item
            db_manager.get_collection('glossary').delete_many({'document_id': doc_id, 'term': name})
        return coll.delete_one({'_id': concept_id})
