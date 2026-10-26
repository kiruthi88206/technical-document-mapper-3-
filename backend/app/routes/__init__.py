from .document_routes import document_bp
from .terminology_routes import terminology_bp
from .concept_routes import concept_bp
from .graph_routes import graph_bp
from .search_routes import search_bp
from .export_routes import export_bp
from .dashboard_routes import dashboard_bp
from .auth_routes import auth_bp

__all__ = [
    "document_bp",
    "terminology_bp",
    "concept_bp",
    "graph_bp",
    "search_bp",
    "export_bp",
    "dashboard_bp",
    "auth_bp"
]
