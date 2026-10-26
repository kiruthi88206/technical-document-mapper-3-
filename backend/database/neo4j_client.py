import logging
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase, Driver
from ..config import settings

logger = logging.getLogger("neo4j_client")

class Neo4jClient:
    """Manages connection and parameterized Cypher queries to Neo4j Graph DB."""

    def __init__(self):
        self.driver: Optional[Driver] = None
        self.is_connected: bool = False
        self.init_driver()

    def init_driver(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                connection_timeout=2.0,
                max_connection_lifetime=30
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            self.is_connected = True
            logger.info("Successfully connected to Neo4j database.")
        except Exception as e:
            self.is_connected = False
            self.driver = None
            logger.warning(f"Neo4j is not connected ({e}). Using local in-memory graph store.")

    def check_connection(self) -> bool:
        if self.driver is None:
            return False
        try:
            self.driver.verify_connectivity()
            self.is_connected = True
            return True
        except Exception:
            self.is_connected = False
            return False

    def close(self):
        if self.driver is not None:
            self.driver.close()
            self.is_connected = False

    def store_document_graph(
        self, 
        doc_id: str, 
        metadata: Dict[str, Any], 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ) -> bool:
        """Store document, concepts, and relationships using parameterized Cypher transactions."""
        if not self.check_connection() or not self.driver:
            return False

        cypher_doc = """
        MERGE (d:Document {id: $doc_id})
        ON CREATE SET d.filename = $filename,
                      d.created_at = datetime(),
                      d.char_count = $char_count,
                      d.word_count = $word_count
        ON MATCH SET  d.filename = $filename,
                      d.updated_at = datetime()
        """

        cypher_concept = """
        MERGE (c:Concept {document_id: $doc_id, concept_id: $id})
        SET c.label = $label,
            c.category = $category,
            c.frequency = $frequency,
            c.tfidf_score = $tfidf_score,
            c.importance_score = $importance_score,
            c.definition = $definition
        WITH c
        MATCH (d:Document {id: $doc_id})
        MERGE (d)-[:CONTAINS]->(c)
        """

        cypher_edge = """
        MATCH (c1:Concept {document_id: $doc_id, concept_id: $from_id})
        MATCH (c2:Concept {document_id: $doc_id, concept_id: $to_id})
        MERGE (c1)-[r:RELATES_TO {id: $edge_id}]->(c2)
        SET r.label = $label,
            r.type = $type,
            r.weight = $weight,
            r.confidence = $confidence,
            r.evidence = $evidence
        """

        try:
            with self.driver.session() as session:
                # 1. Document Node
                session.run(
                    cypher_doc, 
                    doc_id=doc_id, 
                    filename=metadata.get("filename", "unknown"),
                    char_count=metadata.get("char_count", 0),
                    word_count=metadata.get("word_count", 0)
                )

                # 2. Concept Nodes
                for node in nodes:
                    session.run(
                        cypher_concept,
                        doc_id=doc_id,
                        id=str(node["id"]),
                        label=node["label"],
                        category=node["category"],
                        frequency=node.get("frequency", 1),
                        tfidf_score=node.get("tfidf_score", 0.0),
                        importance_score=node.get("importance_score", 0.0),
                        definition=node.get("definition", "")
                    )

                # 3. Relationship Edges
                for edge in edges:
                    session.run(
                        cypher_edge,
                        doc_id=doc_id,
                        from_id=str(edge["from"]),
                        to_id=str(edge["to"]),
                        edge_id=edge.get("id", ""),
                        label=edge.get("label", "relates to"),
                        type=edge.get("type", "co-occurrence"),
                        weight=edge.get("weight", 1),
                        confidence=edge.get("confidence", 0.5),
                        evidence=edge.get("evidence", "")
                    )
            return True
        except Exception as e:
            logger.error(f"Error persisting graph to Neo4j: {e}")
            return False

    def query_graph(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve graph nodes and relationships from Neo4j."""
        if not self.check_connection() or not self.driver:
            return None

        cypher_fetch = """
        MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(c:Concept)
        OPTIONAL MATCH (c)-[r:RELATES_TO]->(c2:Concept {document_id: $doc_id})
        RETURN c, r, c2
        """
        try:
            nodes_dict = {}
            edges = []
            with self.driver.session() as session:
                results = session.run(cypher_fetch, doc_id=doc_id)
                for record in results:
                    c = record["c"]
                    cid = c["concept_id"]
                    if cid not in nodes_dict:
                        nodes_dict[cid] = {
                            "id": cid,
                            "label": c["label"],
                            "category": c["category"],
                            "frequency": c["frequency"],
                            "tfidf_score": c["tfidf_score"],
                            "importance_score": c["importance_score"],
                            "definition": c["definition"]
                        }
                    
                    r = record["r"]
                    c2 = record["c2"]
                    if r is not None and c2 is not None:
                        edges.append({
                            "id": r["id"],
                            "from": cid,
                            "to": c2["concept_id"],
                            "label": r["label"],
                            "type": r["type"],
                            "weight": r["weight"],
                            "confidence": r["confidence"],
                            "evidence": r["evidence"]
                        })

            return {"nodes": list(nodes_dict.values()), "edges": edges}
        except Exception as e:
            logger.error(f"Error querying Neo4j: {e}")
            return None
