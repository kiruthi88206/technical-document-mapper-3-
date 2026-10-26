"""
Graph Construction and Network Analysis Engine.
Uses NetworkX for mathematical graph construction, centrality computations, and
community detection, formatting the output for Vis.js interactive rendering.
"""
from typing import List, Dict, Any, Tuple
import networkx as nx

# Category Color Palette designed for modern dark dashboard theme
CATEGORY_COLORS = {
    "Models & Algorithms": {
        "background": "#6366F1",  # Vibrant Indigo
        "border": "#4338CA",
        "highlight": {"background": "#818CF8", "border": "#C7D2FE"}
    },
    "Data & Representations": {
        "background": "#0EA5E9",  # Vivid Cyan/Sky
        "border": "#0369A1",
        "highlight": {"background": "#38BDF8", "border": "#BAE6FD"}
    },
    "Architectures & Infrastructure": {
        "background": "#10B981",  # Emerald Green
        "border": "#047857",
        "highlight": {"background": "#34D399", "border": "#A7F3D0"}
    },
    "Techniques & Methods": {
        "background": "#EC4899",  # Pink / Magenta
        "border": "#BE185D",
        "highlight": {"background": "#F472B6", "border": "#FBCFE8"}
    },
    "Core Concepts": {
        "background": "#F59E0B",  # Warm Amber
        "border": "#B45309",
        "highlight": {"background": "#FBBF24", "border": "#FDE68A"}
    },
    "Document Structure": {
        "background": "#8B5CF6",  # Violet
        "border": "#6D28D9",
        "highlight": {"background": "#A78BFA", "border": "#DDD6FE"}
    }
}

DEFAULT_COLOR = {
    "background": "#64748B",
    "border": "#334155",
    "highlight": {"background": "#94A3B8", "border": "#CBD5E1"}
}


class KnowledgeGraphBuilder:
    """Builds and analyzes knowledge graphs using NetworkX and formats for Vis.js."""

    @staticmethod
    def build_graph(
        concepts: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build NetworkX graph, compute topological metrics, and format for frontend.
        """
        G = nx.DiGraph()

        # Add nodes
        concept_dict = {}
        for c in concepts:
            cid = str(c.get("concept_id") or c.get("id"))
            concept_dict[cid] = c
            G.add_node(
                cid,
                label=c.get("name", "Unknown"),
                category=c.get("category", "Core Concepts"),
                frequency=c.get("frequency", 1),
                tfidf_score=c.get("tfidf_score", 1.0),
                definition=c.get("definition", "")
            )

        # Add edges
        for rel in relationships:
            src = str(rel.get("source_id") or rel.get("from"))
            dst = str(rel.get("target_id") or rel.get("to"))
            
            # Ensure both nodes exist
            if src in concept_dict and dst in concept_dict:
                G.add_edge(
                    src,
                    dst,
                    label=rel.get("relation_type", "related_to"),
                    category=rel.get("category", "General"),
                    confidence=rel.get("confidence", 0.7),
                    evidence=rel.get("evidence", ""),
                    method=rel.get("method", "Contextual Analysis")
                )

        # Compute graph metrics safely
        degree_centrality = {}
        betweenness_centrality = {}
        pagerank_scores = {}
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()

        if num_nodes > 0:
            try:
                degree_centrality = nx.degree_centrality(G)
            except Exception:
                degree_centrality = {n: 0.1 for n in G.nodes()}

            try:
                betweenness_centrality = nx.betweenness_centrality(G)
            except Exception:
                betweenness_centrality = {n: 0.1 for n in G.nodes()}

            try:
                pagerank_scores = nx.pagerank(G, alpha=0.85, max_iter=100)
            except Exception:
                pagerank_scores = {n: 1.0 / num_nodes for n in G.nodes()}

        # Build Vis.js Nodes
        vis_nodes = []
        for node_id in G.nodes():
            raw_c = concept_dict.get(node_id, {})
            category = raw_c.get("category", "Core Concepts")
            color_scheme = CATEGORY_COLORS.get(category, DEFAULT_COLOR)
            
            deg = G.degree(node_id)
            pr = pagerank_scores.get(node_id, 0.05)
            # Scale node size based on importance/centrality (20 to 55)
            size = min(55, max(22, int(20 + (deg * 4) + (pr * 50))))

            # Rich HTML tooltip
            tooltip = (
                f"<div style='font-family:Inter,sans-serif; padding:6px; max-width:260px;'>"
                f"<div style='font-weight:700; font-size:14px; color:#F8FAFC; margin-bottom:4px;'>{raw_c.get('name')}</div>"
                f"<div style='font-size:11px; color:#94A3B8; margin-bottom:6px;'><span style='background:#334155; padding:2px 6px; border-radius:4px;'>{category}</span></div>"
                f"<div style='font-size:12px; color:#CBD5E1; margin-bottom:6px;'>{raw_c.get('definition', '')[:140]}...</div>"
                f"<div style='font-size:11px; color:#64748B;'>Frequency: <b>{raw_c.get('frequency', 1)}</b> | Degree: <b>{deg}</b></div>"
                f"</div>"
            )

            vis_nodes.append({
                "id": node_id,
                "label": raw_c.get("name", node_id),
                "category": category,
                "value": size,
                "title": tooltip,
                "color": {
                    "background": color_scheme["background"],
                    "border": color_scheme["border"],
                    "highlight": color_scheme["highlight"]
                },
                "font": {
                    "color": "#F8FAFC",
                    "size": 13,
                    "face": "Inter, system-ui, sans-serif"
                },
                "shadow": {
                    "enabled": True,
                    "color": "rgba(0,0,0,0.45)",
                    "size": 7,
                    "x": 2,
                    "y": 2
                },
                "shape": "dot",
                "frequency": raw_c.get("frequency", 1),
                "tfidf_score": raw_c.get("tfidf_score", 0),
                "degree": deg,
                "centrality": round(degree_centrality.get(node_id, 0.0), 3),
                "definition": raw_c.get("definition", "")
            })

        # Build Vis.js Edges
        vis_edges = []
        edge_id_counter = 1
        for u, v, data in G.edges(data=True):
            conf = data.get("confidence", 0.75)
            rel_type = data.get("label", "related_to")
            is_semantic = rel_type in ("semantically_similar", "co_occurs_with")

            tooltip = (
                f"<div style='font-family:Inter,sans-serif; padding:4px; max-width:240px;'>"
                f"<div style='font-weight:600; color:#F8FAFC;'>Relation: {rel_type}</div>"
                f"<div style='font-size:11px; color:#94A3B8;'>Confidence: {int(conf * 100)}%</div>"
                f"<div style='font-size:11px; color:#CBD5E1; margin-top:4px;'>Evidence: {data.get('evidence', '')[:120]}</div>"
                f"</div>"
            )

            vis_edges.append({
                "id": f"e_{edge_id_counter}",
                "from": u,
                "to": v,
                "label": rel_type.replace("_", " "),
                "title": tooltip,
                "arrows": {
                    "to": {
                        "enabled": True,
                        "scaleFactor": 0.8
                    }
                },
                "width": max(1.2, conf * 2.8),
                "dashes": is_semantic,
                "color": {
                    "color": "#64748B" if is_semantic else "#818CF8",
                    "highlight": "#38BDF8",
                    "hover": "#A5B4FC"
                },
                "font": {
                    "color": "#94A3B8",
                    "size": 10,
                    "align": "middle",
                    "strokeWidth": 2,
                    "strokeColor": "#0F172A"
                },
                "smooth": {
                    "type": "continuous",
                    "roundness": 0.15
                },
                "confidence": conf,
                "relation_type": rel_type,
                "category": data.get("category", "General"),
                "evidence": data.get("evidence", "")
            })
            edge_id_counter += 1

        # Graph Metrics Summary
        density = round(nx.density(G), 3) if num_nodes > 1 else 0
        connected_components_count = nx.number_weakly_connected_components(G) if num_nodes > 0 else 0

        # Find most central hub concept
        hub_concept = "None"
        if degree_centrality:
            top_hub_id = max(degree_centrality, key=degree_centrality.get)
            hub_concept = concept_dict.get(top_hub_id, {}).get("name", "None")

        return {
            "nodes": vis_nodes,
            "edges": vis_edges,
            "metrics": {
                "node_count": num_nodes,
                "edge_count": num_edges,
                "density": density,
                "connected_components": connected_components_count,
                "primary_hub": hub_concept
            }
        }
