import firebase_admin
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError
from backend.firebase_db import get_firestore_db
from backend.models import UserInDB, UserBase
import jwt
import os
from datetime import datetime, timedelta
from flask import current_app

users_ref = lambda: get_firestore_db().collection('users')

def generate_jwt_token(user_id: str):
    """Generates a JWT for the Flask API."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7),  # Token expiry: 7 days
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")

def decode_jwt_token(token: str):
    """Decodes a JWT token."""
    # Ensure current_app is imported from flask
    return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])


def register_user_and_get_token(id_token: str):
    """Registers user in Firebase (implicitly) and your Firestore, then returns JWT."""
    try:
        decoded_token = auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email')
        username = decoded_token.get('name', email.split('@')[0] if email else firebase_uid) # Default username

        # Check if user already exists in Firestore by firebase_uid
        user_query = users_ref().where('firebase_uid', '==', firebase_uid).limit(1).get()
        user_doc_id = None
        user_data = {}

        if user_query:
            # User already exists in your Firestore, retrieve their internal ID
            user_doc = user_query[0]
            user_doc_id = user_doc.id
            user_data = user_doc.to_dict()
            print(f"User with Firebase UID {firebase_uid} already exists in Firestore. ID: {user_doc_id}")
        else:
            # Create a new user document in Firestore
            new_user_data = {
                'firebase_uid': firebase_uid,
                'email': email,
                'username': username,
                'created_at': datetime.utcnow()
            }
            update_time, doc_ref = users_ref().add(new_user_data)
            user_doc_id = doc_ref.id
            user_data = new_user_data # For JWT creation and return
            print(f"New user created in Firestore. ID: {user_doc_id}")

        jwt_token = generate_jwt_token(user_doc_id)
        return jwt_token, UserInDB(doc_id=user_doc_id, **user_data)

    except FirebaseError as e:
        print(f"Firebase Authentication error during registration: {e}")
        raise ValueError("Firebase authentication failed. Invalid token or user details.")
    except Exception as e:
        print(f"Error during registration: {e}")
        raise

def login_user_and_get_token(id_token: str):
    """Logs in user via Firebase, verifies their existence in Firestore, then returns JWT."""
    try:
        decoded_token = auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']

        # Find user in Firestore by firebase_uid
        user_query = users_ref().where('firebase_uid', '==', firebase_uid).limit(1).get()
        if not user_query:
            raise ValueError("User not found in database. Please register first.")

        user_doc = user_query[0]
        user_doc_id = user_doc.id
        user_data = user_doc.to_dict()

        jwt_token = generate_jwt_token(user_doc_id)
        return jwt_token, UserInDB(doc_id=user_doc_id, **user_data)

    except FirebaseError as e:
        print(f"Firebase Authentication error during login: {e}")
        raise ValueError("Firebase authentication failed. Invalid token.")
    except Exception as e:
        print(f"Error during login: {e}")
        raise

def get_current_user_from_db(user_id: str):
    """Retrieves user details from Firestore using internal user_id."""
    try:
        user_doc = users_ref().document(user_id).get()
        if user_doc.exists:
            return UserInDB(doc_id=user_doc.id, **user_doc.to_dict())
        return None
    except Exception as e:
        print(f"Error fetching user {user_id} from Firestore: {e}")
        return None