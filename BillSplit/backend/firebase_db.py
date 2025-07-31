import firebase_admin
from firebase_admin import credentials, firestore
import os
from flask import current_app # Needed for app.config and root_path

_db_instance = None # Use a private variable to hold the instance

def initialize_firebase_app():
    global _db_instance
    if _db_instance is not None:
        # Already initialized, return the existing instance
        return _db_instance

    if firebase_admin._apps:
        if 'default' in firebase_admin._apps:
            # App is already initialized, just get the client
            _db_instance = firestore.client()
            return _db_instance

    try:
        # Path to your Firebase Admin SDK service account key
        # We need to be careful with the path if running from parent directory
        # current_app.root_path will be `BillSplit/backend`
        # so `os.path.join(current_app.root_path, 'instance', 'firebase_admin_key.json')`
        # is the correct way to build the path relative to the app's root module.
        default_cred_path = os.path.join(current_app.root_path, 'instance', 'firebase_admin_key.json')
        cred_path = current_app.config.get("FIREBASE_ADMIN_SDK_PATH", default_cred_path)

        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase Admin SDK key file not found at: {cred_path}")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _db_instance = firestore.client() # Assign to the private global
        print("Firebase Admin SDK initialized successfully.")
        return _db_instance # Return the instance
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        # Re-raise the exception to clearly indicate failure
        raise

def get_firestore_db():
    """Provides the Firestore client instance, initializing if necessary."""
    global _db_instance
    if _db_instance is None:
        # Attempt to initialize if not already initialized
        # This might be too late if app context isn't fully set up,
        # so ensure initialize_firebase_app is called during Flask app startup.
        try:
            _db_instance = initialize_firebase_app()
        except Exception:
            # If initialization fails here, it means app startup wasn't robust enough
            raise RuntimeError("Firestore DB not initialized. Check Flask app setup.")
    return _db_instance

# Make sure db is imported as a function call
# So, in other files, you'll call firebase_db.get_firestore_db()
# or import `db = get_firestore_db()`