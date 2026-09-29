import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lms-secret-key-2024-change-in-production'
    
    raw_db_url = os.environ.get('DATABASE_URL')
    if raw_db_url:
        # Standardize PostgreSQL URLs for SQLAlchemy with pg8000 (pure-python, Vercel-compatible)
        if raw_db_url.startswith('postgres://'):
            db_url = raw_db_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif raw_db_url.startswith('postgresql://') and not raw_db_url.startswith('postgresql+'):
            db_url = raw_db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        else:
            db_url = raw_db_url
    else:
        # If on Vercel / AWS Lambda without custom DB, use writable /tmp directory
        if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            db_url = 'sqlite:////tmp/library.db'
        else:
            db_url = 'sqlite:///library.db'
            
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID')
    
    # Library Settings (can be overridden from DB)
    LIBRARY_NAME = 'LPU Library Management'
    LIBRARY_ADDRESS = '123 University Road, Academic City'
    LIBRARY_EMAIL = 'library@university.edu'
    LIBRARY_PHONE = '+91-9876543210'
    FINE_PER_DAY = 5  # INR
    MAX_BOOKS_PER_MEMBER = 5
    DEFAULT_BORROW_DAYS = 14
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
