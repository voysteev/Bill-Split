import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_super_secret_key_please_change_this_in_production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    # Firebase Admin SDK Path (relative to project root or absolute)
    FIREBASE_ADMIN_SDK_PATH = os.environ.get('FIREBASE_ADMIN_SDK_PATH', 'instance/firebase_admin_key.json')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key_please_change_this_in_production')