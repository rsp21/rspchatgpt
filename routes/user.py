from flask import Blueprint, jsonify

user_bp = Blueprint('user', __name__)

@user_bp.route("/user/info", methods=["GET"])
def get_user_info():
    # Placeholder response for now
    return jsonify({
        "user_id": "12345",
        "name": "Jane Doe",
        "status": "Demo route active ✅"
    })
