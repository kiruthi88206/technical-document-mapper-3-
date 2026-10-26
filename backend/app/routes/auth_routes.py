from flask import Blueprint, request, jsonify
from ..database import get_db
from ..models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def ensure_demo_user():
    """Ensure a default demo user exists for seamless testing."""
    session = get_db()
    demo_user = session.query(User).filter_by(email="demo@docmapper.ai").first()
    if not demo_user:
        user = User(
            email="demo@docmapper.ai",
            name="Dr. Alex Morgan",
            role="Lead NLP Researcher"
        )
        user.set_password("demo123")
        session.add(user)
        session.commit()

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    name = data.get("name", "").strip()
    password = data.get("password", "")

    if not email or "@" not in email:
        return jsonify({"error": "A valid email address is required.", "status": 400}), 400
    if not name:
        return jsonify({"error": "Full name is required.", "status": 400}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters.", "status": 400}), 400

    session = get_db()
    existing = session.query(User).filter_by(email=email).first()
    if existing:
        return jsonify({"error": "An account with this email already exists.", "status": 409}), 409

    user = User(email=email, name=name, role="Technical Analyst")
    user.set_password(password)
    session.add(user)
    session.commit()

    return jsonify({
        "success": True,
        "message": "Account created successfully.",
        "user": user.to_dict(),
        "token": f"token-{user.id}"
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    ensure_demo_user()
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required.", "status": 400}), 400

    session = get_db()
    user = session.query(User).filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password.", "status": 401}), 401

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": user.to_dict(),
        "token": f"token-{user.id}"
    })

@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    ensure_demo_user()
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer token-"):
        user_id = auth_header.replace("Bearer token-", "").strip()
        session = get_db()
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            return jsonify({"success": True, "user": user.to_dict()})

    # Return default demo user as fallback
    session = get_db()
    demo_user = session.query(User).filter_by(email="demo@docmapper.ai").first()
    return jsonify({
        "success": True,
        "user": demo_user.to_dict() if demo_user else {
            "id": "demo-id",
            "name": "Demo Researcher",
            "email": "demo@docmapper.ai",
            "role": "Lead NLP Analyst"
        }
    })
