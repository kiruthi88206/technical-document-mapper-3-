import uuid
from datetime import datetime
from database.mongodb import db_manager

class DocumentModel:
    @staticmethod
    def create(filename, file_path, file_type, file_size, summary=""):
        doc_id = str(uuid.uuid4())
        doc_data = {
            '_id': doc_id,
            'filename': filename,
            'file_path': file_path,
            'file_type': file_type,
            'file_size': file_size,
            'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'uploaded',
            'summary': summary,
            'stats': {
                'terms_count': 0,
                'concepts_count': 0,
                'relationships_count': 0
            }
        }
        coll = db_manager.get_collection('documents')
        coll.insert_one(doc_data)
        return doc_data

    @staticmethod
    def get_by_id(doc_id):
        coll = db_manager.get_collection('documents')
        return coll.find_one({'_id': doc_id})

    @staticmethod
    def get_all():
        coll = db_manager.get_collection('documents')
        return coll.find()

    @staticmethod
    def update_status(doc_id, status, stats=None, summary=None):
        coll = db_manager.get_collection('documents')
        update_fields = {'status': status}
        if stats:
            update_fields['stats'] = stats
        if summary:
            update_fields['summary'] = summary
        coll.update_one({'_id': doc_id}, {'$set': update_fields})

    @staticmethod
    def delete(doc_id):
        coll = db_manager.get_collection('documents')
        # Also clean up concepts, relationships, glossary
        db_manager.get_collection('concepts').delete_many({'document_id': doc_id})
        db_manager.get_collection('relationships').delete_many({'document_id': doc_id})
        db_manager.get_collection('glossary').delete_many({'document_id': doc_id})
        return coll.delete_one({'_id': doc_id})
