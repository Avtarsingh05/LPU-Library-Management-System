import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lms-secret-key-2024-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///library.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Library Settings (can be overridden from DB)
    LIBRARY_NAME = 'LPU Library Management'
    LIBRARY_ADDRESS = 'Lovely Professional University, Phagwara'
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
