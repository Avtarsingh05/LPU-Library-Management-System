import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lms-secret-key-2024-change-in-production'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Firebase client-side config (for frontend Google Sign-In)
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID')

    # Library defaults (overridable via Firestore settings collection)
    LIBRARY_NAME = 'LPU Library'
    FINE_PER_DAY = 5
    MAX_BOOKS_PER_MEMBER = 5
    DEFAULT_BORROW_DAYS = 14


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}

