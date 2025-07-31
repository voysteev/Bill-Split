from flask import Blueprint, request, jsonify, current_app
from backend.services import auth_service
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def jwt_required(f):
    """A decorator to protect API routes with JWT authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "Authorization token is missing!"}), 401

        try:
            token = auth_header.split(" ")[1]
            payload = auth_service.decode_jwt_token(token) # Need to implement this in auth_service
            request.user_id = payload['user_id'] # Attach user_id to request object
        except ExpiredSignatureError:
            return jsonify({"message": "Token has expired."}), 401
        except InvalidTokenError:
            return jsonify({"message": "Invalid token."}), 401
        except IndexError:
            return jsonify({"message": "Token format is invalid."}), 401
        except Exception as e:
            return jsonify({"message": f"Authentication error: {e}"}), 500

        return f(*args, **kwargs)
    return decorated_function

# Add decode_jwt_token to auth_service.py for the decorator to work
# backend/services/auth_service.py
# ...
# def decode_jwt_token(token: str):
#     return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
# ...


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    id_token = data.get('idToken')
    if not id_token:
        return jsonify({"message": "idToken is required."}), 400

    try:
        jwt_token, user_data = auth_service.register_user_and_get_token(id_token)
        return jsonify({
            "message": "User registered successfully!",
            "token": jwt_token,
            "user": user_data.model_dump(by_alias=True) # Use by_alias to show 'id' instead of 'doc_id'
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({"message": "An error occurred during registration."}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    id_token = data.get('idToken')
    if not id_token:
        return jsonify({"message": "idToken is required."}), 400

    try:
        jwt_token, user_data = auth_service.login_user_and_get_token(id_token)
        return jsonify({
            "message": "User logged in successfully!",
            "token": jwt_token,
            "user": user_data.model_dump(by_alias=True)
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 401 # Unauthorized for login failures
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({"message": "An error occurred during login."}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    user_id = request.user_id
    try:
        user = auth_service.get_current_user_from_db(user_id)
        if user:
            return jsonify(user.model_dump(by_alias=True)), 200
        return jsonify({"message": "User not found."}), 404
    except Exception as e:
        current_app.logger.error(f"Error fetching current user: {e}")
        return jsonify({"message": "An error occurred."}), 500