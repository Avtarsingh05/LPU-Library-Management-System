"""
Firestore database initialization.
Replaces SQLAlchemy. All data stored in Firebase Firestore.
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore as firebase_firestore

_db = None

def get_db():
    """Return the Firestore client, initializing Firebase Admin SDK if needed."""
    global _db
    if _db is not None:
        return _db

    # Initialize Firebase Admin if not already done
    if not firebase_admin._apps:
        sa_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if sa_json:
            try:
                sa_dict = json.loads(sa_json)
                cred = credentials.Certificate(sa_dict)
            except Exception as e:
                raise RuntimeError(f"Invalid FIREBASE_SERVICE_ACCOUNT JSON: {e}")
        else:
            # Try default credentials (for local development with GOOGLE_APPLICATION_CREDENTIALS)
            try:
                cred = credentials.ApplicationDefault()
            except Exception:
                raise RuntimeError(
                    "No Firebase credentials found. Set FIREBASE_SERVICE_ACCOUNT env var "
                    "with your service account JSON string."
                )
        firebase_admin.initialize_app(cred)

    _db = firebase_firestore.client()
    return _db
