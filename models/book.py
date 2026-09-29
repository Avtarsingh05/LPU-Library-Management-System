from . import db
from datetime import datetime

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(150))
    publication_year = db.Column(db.Integer)
    language = db.Column(db.String(50), default='English')
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    shelf_location = db.Column(db.String(50))
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    issues = db.relationship('Issue', backref='book', lazy='dynamic')
    reservations = db.relationship('Reservation', backref='book', lazy='dynamic')
    
    @property
    def issued_copies(self):
        return self.total_copies - self.available_copies
    
    @property
    def is_available(self):
        return self.available_copies > 0
    
    def __repr__(self):
        return f'<Book {self.title}>'
