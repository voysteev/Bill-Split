import os
from flask import Flask, jsonify
from flask_cors import CORS
from backend.firebase_db import initialize_firebase_app

# Import blueprints
from backend.routes.auth import auth_bp
from backend.routes.groups import groups_bp
from backend.routes.expenses import expenses_bp
from backend.routes.settlements import settlements_bp

app = Flask(__name__, instance_relative_config=True)
CORS(app)

app.config.from_object('backend.config.Config')
app.config.from_pyfile('instance/config.py', silent=True)


# Initialize Firebase Admin SDK for Firestore.
# This must happen within the Flask app context because it might read app.config.
with app.app_context():
    try:
        # Call the initialization function
        initialize_firebase_app()
    except Exception as e:
        app.logger.critical(f"Failed to initialize Firebase Admin SDK: {e}")
        # Depending on criticality, you might want to exit or log heavily

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(groups_bp, url_prefix='/api/groups')
app.register_blueprint(expenses_bp, url_prefix='/api/expenses')
app.register_blueprint(settlements_bp, url_prefix='/api/settlements')

@app.route('/')
def index():
    return "BillSplit Backend Running!"

# Error Handlers (Optional but Recommended)
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"message": "Bad request.", "error": str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"message": "Unauthorized access."}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({"message": "Forbidden access."}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found."}), 404

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.exception('An internal server error occurred', exc_info=error)
    return jsonify({"message": "An internal server error occurred."}), 500

if __name__ == '__main__':
    # To run: navigate to BillSplit/backend in terminal and run `flask run`
    # Or, if you prefer, `python app.py` (ensure FLASK_APP and FLASK_DEBUG are set in env)
    app.run(debug=True) # debug=True is good for development