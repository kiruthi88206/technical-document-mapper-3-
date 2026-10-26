import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from .config import Config
from .database import init_db, db_session

def create_app(test_config=None):
    """
    Application factory for the Technical Document Terminology and Concept Relationship Mapper.
    """
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
    has_frontend = os.path.exists(frontend_dist)

    app = Flask(
        __name__,
        static_folder=frontend_dist if has_frontend else None,
        static_url_path="/"
    )

    if test_config:
        app.config.update(test_config)
    else:
        app.config.from_object(Config)

    # Enable CORS for frontend dev server and API clients
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize SQLAlchemy database tables
    with app.app_context():
        init_db()

    # Teardown database session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Health check
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "online",
            "app": Config.PROJECT_NAME,
            "version": Config.VERSION,
            "database": "SQLite (SQLAlchemy 2.0)",
            "pipeline": "Active"
        })

    # Register API Blueprints
    from .routes import (
        document_bp,
        terminology_bp,
        concept_bp,
        graph_bp,
        search_bp,
        export_bp,
        dashboard_bp,
        auth_bp
    )

    app.register_blueprint(document_bp)
    app.register_blueprint(terminology_bp)
    app.register_blueprint(concept_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)

    # SPA Frontend fallback routes
    if has_frontend:
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            if path and os.path.exists(os.path.join(frontend_dist, path)):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, "index.html")

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": getattr(e, "description", "Bad request"), "status": 400}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({"error": "File size exceeds the configured upload limit.", "status": 413}), 413

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"error": getattr(e, "description", "Unprocessable entity"), "status": 422}), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "An internal server error occurred.", "status": 500}), 500

    return app
