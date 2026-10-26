import uuid
from database.mongodb import db_manager

class RelationshipModel:
    @staticmethod
    def create_many(relationships_list):
        if not relationships_list:
            return []
        coll = db_manager.get_collection('relationships')
        inserted = []
        for item in relationships_list:
            if '_id' not in item:
                item['_id'] = str(uuid.uuid4())
            coll.insert_one(item)
            inserted.append(item)
        return inserted

    @staticmethod
    def get_by_document(doc_id):
        coll = db_manager.get_collection('relationships')
        return coll.find({'document_id': doc_id})

    @staticmethod
    def update(relationship_id, update_data):
        coll = db_manager.get_collection('relationships')
        return coll.update_one({'_id': relationship_id}, {'$set': update_data})

    @staticmethod
    def delete(relationship_id):
        coll = db_manager.get_collection('relationships')
        return coll.delete_one({'_id': relationship_id})
