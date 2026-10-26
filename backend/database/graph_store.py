import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import networkx as nx
from .neo4j_client import Neo4jClient

class GraphStore:
    """
    Central repository for graph models, analytics, and metadata.
    Coordinates between Neo4j and local fallback storage.
    """

    def __init__(self):
        self.neo4j = Neo4jClient()
        # In-memory document storage: doc_id -> { "metadata": ..., "nodes": ..., "edges": ..., "nx_graph": ... }
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_database_status(self) -> Dict[str, Any]:
        """Return connectivity details for database transparency."""
        is_neo4j = self.neo4j.check_connection()
        return {
            "mode": "neo4j" if is_neo4j else "in-memory-fallback",
            "connected": is_neo4j,
            "provider": "Neo4j Graph Database" if is_neo4j else "Local In-Memory NetworkX Store",
            "message": "Neo4j is actively connected." if is_neo4j else "Neo4j offline. Running with resilient local graph engine."
        }

    def save_graph(
        self, 
        doc_id: str, 
        metadata: Dict[str, Any], 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ):
        """Save graph data in local cache and persist to Neo4j if available."""
        # 1. Build NetworkX graph for topology metrics
        g = nx.Graph()
        for n in nodes:
            g.add_node(str(n["id"]), **n)
        for e in edges:
            g.add_edge(str(e["from"]), str(e["to"]), **e)

        # Compute graph analytics
        degree_dict = dict(g.degree())
        betweenness = nx.betweenness_centrality(g) if len(g) > 2 else {}
        density = round(nx.density(g), 4) if len(g) > 1 else 0.0
        connected_components = nx.number_connected_components(g) if len(g) > 0 else 0

        # Enrich node metrics
        for n in nodes:
            nid = str(n["id"])
            n["degree"] = degree_dict.get(nid, 0)
            n["centrality"] = round(betweenness.get(nid, 0.0), 4)

        # Store in local memory cache
        self._cache[doc_id] = {
            "document_id": doc_id,
            "metadata": {
                **metadata,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "node_count": len(nodes),
                "edge_count": len(edges),
                "density": density,
                "connected_components": connected_components
            },
            "nodes": nodes,
            "edges": edges,
            "nx_graph": g
        }

        # Try persisting to Neo4j
        if self.neo4j.is_connected:
            self.neo4j.store_document_graph(doc_id, metadata, nodes, edges)

    def get_graph(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve graph and document metadata."""
        if doc_id in self._cache:
            data = self._cache[doc_id]
            return {
                "document_id": doc_id,
                "metadata": data["metadata"],
                "nodes": data["nodes"],
                "edges": data["edges"],
                "database_status": self.get_database_status()
            }
        
        # Try fetching from Neo4j if not in local cache
        if self.neo4j.is_connected:
            neo4j_res = self.neo4j.query_graph(doc_id)
            if neo4j_res:
                return {
                    "document_id": doc_id,
                    "metadata": {"id": doc_id, "source": "neo4j"},
                    "nodes": neo4j_res["nodes"],
                    "edges": neo4j_res["edges"],
                    "database_status": self.get_database_status()
                }

        return None

    def get_glossary(self, doc_id: str) -> Optional[List[Dict[str, Any]]]:
        """Return structured glossary list."""
        if doc_id not in self._cache:
            return None
        nodes = self._cache[doc_id]["nodes"]
        # Format as glossary sorted by importance
        glossary = []
        for n in sorted(nodes, key=lambda x: x.get("importance_score", 0), reverse=True):
            glossary.append({
                "id": n["id"],
                "term": n["label"],
                "category": n["category"],
                "frequency": n.get("frequency", 1),
                "tfidf_score": n.get("tfidf_score", 0.0),
                "importance_score": n.get("importance_score", 0.0),
                "definition": n.get("definition", ""),
                "contexts": n.get("contexts", [])
            })
        return glossary

    def search_concepts(self, doc_id: str, query: str) -> Dict[str, Any]:
        """Search for concepts by term or category, returning matched nodes and 1-hop neighbors."""
        if doc_id not in self._cache:
            return {"matches": [], "neighbors": [], "subgraph": {"nodes": [], "edges": []}}

        data = self._cache[doc_id]
        nodes = data["nodes"]
        edges = data["edges"]
        q = query.lower().strip()

        matched_node_ids = set()
        matched_nodes = []
        for n in nodes:
            if q in n["label"].lower() or q in n["category"].lower() or q in n.get("definition", "").lower():
                matched_node_ids.add(str(n["id"]))
                matched_nodes.append(n)

        # Find 1-hop connected neighbors
        neighbor_ids = set()
        connected_edges = []
        for e in edges:
            f = str(e["from"])
            t = str(e["to"])
            if f in matched_node_ids or t in matched_node_ids:
                connected_edges.append(e)
                if f not in matched_node_ids:
                    neighbor_ids.add(f)
                if t not in matched_node_ids:
                    neighbor_ids.add(t)

        neighbor_nodes = [n for n in nodes if str(n["id"]) in neighbor_ids]
        subgraph_nodes = matched_nodes + neighbor_nodes

        return {
            "query": query,
            "matched_count": len(matched_nodes),
            "matches": matched_nodes,
            "neighbors": neighbor_nodes,
            "subgraph": {
                "nodes": subgraph_nodes,
                "edges": connected_edges
            }
        }

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """List summary of all processed documents."""
        docs = []
        for doc_id, data in self._cache.items():
            meta = data["metadata"]
            docs.append({
                "document_id": doc_id,
                "filename": meta.get("filename", "Untitled Document"),
                "saved_at": meta.get("saved_at", ""),
                "node_count": meta.get("node_count", 0),
                "edge_count": meta.get("edge_count", 0),
                "word_count": meta.get("word_count", 0)
            })
        return docs

# Global singleton
graph_store = GraphStore()
