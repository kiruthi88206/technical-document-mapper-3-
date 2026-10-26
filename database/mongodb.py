import os
import json
import uuid
from datetime import datetime
from config import Config

# Try importing pymongo
try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


class InMemoryCollection:
    """Fallback collection for running without a live MongoDB instance."""
    def __init__(self, name):
        self.name = name
        self._data = {}

    def insert_one(self, doc):
        doc = dict(doc)
        if '_id' not in doc or not doc['_id']:
            doc['_id'] = str(uuid.uuid4())
        self._data[doc['_id']] = doc
        class InsertResult:
            inserted_id = doc['_id']
        return InsertResult()

    def find_one(self, filter_dict=None):
        filter_dict = filter_dict or {}
        for doc in self._data.values():
            if self._matches(doc, filter_dict):
                return dict(doc)
        return None

    def find(self, filter_dict=None, sort=None):
        filter_dict = filter_dict or {}
        results = [dict(doc) for doc in self._data.values() if self._matches(doc, filter_dict)]
        if sort:
            field, direction = sort[0]
            results.sort(key=lambda x: x.get(field, ''), reverse=(direction == -1))
        return results

    def update_one(self, filter_dict, update_dict):
        doc = self.find_one(filter_dict)
        if doc and doc.get('_id'):
            target_id = doc['_id']
            if '$set' in update_dict:
                for k, v in update_dict['$set'].items():
                    self._data[target_id][k] = v
            class UpdateResult:
                modified_count = 1
            return UpdateResult()
        class UpdateResult:
            modified_count = 0
        return UpdateResult()

    def delete_one(self, filter_dict):
        doc = self.find_one(filter_dict)
        if doc and doc.get('_id'):
            del self._data[doc['_id']]
            class DeleteResult:
                deleted_count = 1
            return DeleteResult()
        class DeleteResult:
            deleted_count = 0
        return DeleteResult()

    def delete_many(self, filter_dict):
        filter_dict = filter_dict or {}
        matching_ids = [doc['_id'] for doc in self._data.values() if self._matches(doc, filter_dict)]
        for doc_id in matching_ids:
            del self._data[doc_id]
        class DeleteResult:
            deleted_count = len(matching_ids)
        return DeleteResult()

    def count_documents(self, filter_dict=None):
        filter_dict = filter_dict or {}
        return sum(1 for doc in self._data.values() if self._matches(doc, filter_dict))

    def create_index(self, keys, **kwargs):
        pass  # No-op for in-memory

    def _matches(self, doc, filter_dict):
        for k, v in filter_dict.items():
            if k == '_id':
                if doc.get('_id') != str(v):
                    return False
            elif doc.get(k) != v:
                return False
        return True


class MongoDatabaseManager:
    def __init__(self):
        self.is_connected = False
        self.db = None
        self.client = None
        self.use_fallback = False
        self._init_connection()

    def _init_connection(self):
        if PYMONGO_AVAILABLE:
            try:
                self.client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=2000)
                # Quick ping to test connection
                self.client.admin.command('ping')
                self.db = self.client[Config.DATABASE_NAME]
                self.is_connected = True
                self._setup_indexes()
                print(f"[MongoDB] Successfully connected to {Config.MONGODB_URI}")
                return
            except Exception as e:
                print(f"[MongoDB] Connection warning ({e}). Falling back to robust internal memory storage.")
        else:
            print("[MongoDB] PyMongo module not installed. Using fallback internal memory storage.")
        
        self.use_fallback = True
        self.db = {
            'documents': InMemoryCollection('documents'),
            'concepts': InMemoryCollection('concepts'),
            'relationships': InMemoryCollection('relationships'),
            'glossary': InMemoryCollection('glossary'),
            'search_history': InMemoryCollection('search_history')
        }

    def _setup_indexes(self):
        if self.is_connected and self.db is not None:
            try:
                self.db['documents'].create_index([('upload_date', DESCENDING)])
                self.db['concepts'].create_index([('document_id', ASCENDING), ('relevance_score', DESCENDING)])
                self.db['relationships'].create_index([('document_id', ASCENDING)])
                self.db['glossary'].create_index([('document_id', ASCENDING), ('term', ASCENDING)])
            except Exception as e:
                print(f"[MongoDB] Index creation warning: {e}")

    def get_collection(self, name):
        if self.use_fallback:
            return self.db[name]
        return self.db[name]

# Singleton instance
db_manager = MongoDatabaseManager()
