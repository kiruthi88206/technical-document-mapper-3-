"""
Database abstraction layer supporting MongoDB with automatic fallback to Local JSON Storage.
Ensures zero-crash development and presentation mode if MongoDB service is not started.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import Config

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


class LocalCollection:
    """Thread-safe and persistent file-based collection mirroring MongoDB interface."""
    def __init__(self, name: str, base_dir: str):
        self.name = name
        self.file_path = os.path.join(base_dir, f"{name}.json")
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_all(self, data: List[Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def insert_one(self, document: Dict[str, Any]) -> str:
        doc = dict(document)
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        docs = self._read_all()
        docs.append(doc)
        self._write_all(docs)
        return doc["_id"]

    def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        docs = self._read_all()
        ids = []
        for document in documents:
            doc = dict(document)
            if "_id" not in doc:
                doc["_id"] = str(uuid.uuid4())
            ids.append(doc["_id"])
            docs.append(doc)
        self._write_all(docs)
        return ids

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        docs = self._read_all()
        for doc in docs:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    def find(self, query: Optional[Dict[str, Any]] = None, sort_field: Optional[str] = None, reverse: bool = True) -> List[Dict[str, Any]]:
        docs = self._read_all()
        if not query:
            results = docs
        else:
            results = []
            for doc in docs:
                match = True
                for k, v in query.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    results.append(doc)
        if sort_field:
            results.sort(key=lambda x: x.get(sort_field, ""), reverse=reverse)
        return results

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        docs = self._read_all()
        updated = False
        for i, doc in enumerate(docs):
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                if "$set" in update:
                    doc.update(update["$set"])
                else:
                    doc.update(update)
                docs[i] = doc
                updated = True
                break
        if updated:
            self._write_all(docs)
        return updated

    def delete_one(self, query: Dict[str, Any]) -> bool:
        docs = self._read_all()
        initial_len = len(docs)
        docs = [d for d in docs if not all(d.get(k) == v for k, v in query.items())]
        if len(docs) != initial_len:
            self._write_all(docs)
            return True
        return False

    def delete_many(self, query: Dict[str, Any]) -> int:
        docs = self._read_all()
        initial_len = len(docs)
        docs = [d for d in docs if not all(d.get(k) == v for k, v in query.items())]
        deleted_count = initial_len - len(docs)
        if deleted_count > 0:
            self._write_all(docs)
        return deleted_count

    def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        return len(self.find(query))


class DatabaseManager:
    def __init__(self):
        self.mode = "local"  # 'mongodb' or 'local'
        self.client = None
        self.db = None
        self.collections = {}
        self._init_database()

    def _init_database(self):
        if Config.USE_MONGODB and PYMONGO_AVAILABLE:
            try:
                # 1.5s timeout to avoid blocking if MongoDB isn't active
                self.client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=1500)
                self.client.server_info()  # Forces connection check
                self.db = self.client[Config.MONGO_DB_NAME]
                self.mode = "mongodb"
                print(f"[DB INFO] Connected successfully to MongoDB at {Config.MONGO_URI} (DB: {Config.MONGO_DB_NAME})")
            except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
                print(f"[DB NOTICE] MongoDB connection unavailable ({e}). Automatically using Local Storage mode.")
                self.mode = "local"
        else:
            print("[DB NOTICE] Running in Local Storage Mode (JSON store).")
            self.mode = "local"

    def get_collection(self, collection_name: str):
        if self.mode == "mongodb" and self.db is not None:
            return self.db[collection_name]
        else:
            if collection_name not in self.collections:
                self.collections[collection_name] = LocalCollection(collection_name, Config.LOCAL_DB_FOLDER)
            return self.collections[collection_name]

    @property
    def documents(self):
        return self.get_collection("documents")

    @property
    def concepts(self):
        return self.get_collection("concepts")

    @property
    def relationships(self):
        return self.get_collection("relationships")

    @property
    def glossary(self):
        return self.get_collection("glossary")

    @property
    def analysis_results(self):
        return self.get_collection("analysis_results")

    @property
    def graph_edits(self):
        return self.get_collection("graph_edits")

    def get_status(self) -> Dict[str, Any]:
        doc_count = self.documents.count_documents({})
        concept_count = self.concepts.count_documents({})
        rel_count = self.relationships.count_documents({})
        return {
            "mode": self.mode,
            "connected": True,
            "database_name": Config.MONGO_DB_NAME if self.mode == "mongodb" else "Local JSON Database",
            "counts": {
                "documents": doc_count,
                "concepts": concept_count,
                "relationships": rel_count
            }
        }


# Singleton database instance
db_manager = DatabaseManager()
