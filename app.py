"""
Technical Document Terminology and Concept Relationship Mapper
Flask Application Entry Point.
"""
import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config import Config
from database.db import db_manager
from routes.api import api_bp


def create_app():
    """Application factory."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static"
    )

    app.config.from_object(Config)
    CORS(app)

    # Register API routes
    app.register_blueprint(api_bp)

    # Frontend Root Route
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health')
    def health_check():
        db_stat = db_manager.get_status()
        return jsonify({
            "status": "healthy",
            "app": "Technical Document Terminology and Concept Relationship Mapper",
            "database": db_stat
        })

    # Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error occurred", "status": 500}), 500

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("=" * 70)
    print("  TECHNICAL DOCUMENT TERMINOLOGY & CONCEPT RELATIONSHIP MAPPER")
    print(f"  Running on: http://127.0.0.1:{port}")
    print(f"  Database Mode: {db_manager.mode.upper()}")
    print("=" * 70)
    app.run(host="0.0.0.0", port=port, debug=True)
