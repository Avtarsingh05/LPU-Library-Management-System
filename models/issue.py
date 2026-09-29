from . import db
from datetime import datetime, date

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='issued')  # issued, returned, overdue
    fine_amount = db.Column(db.Float, default=0.0)
    
    # Relationships
    fines = db.relationship('Fine', backref='issue', lazy='dynamic')
    admin = db.relationship('User', foreign_keys=[issued_by], backref='issued_books')
    
    @property
    def is_overdue(self):
        if self.status == 'issued':
            return date.today() > self.due_date
        return False
    
    @property
    def overdue_days(self):
        if self.is_overdue:
            return (date.today() - self.due_date).days
        elif self.status == 'returned' and self.return_date and self.return_date > self.due_date:
            return (self.return_date - self.due_date).days
        return 0
    
    @property
    def days_remaining(self):
        if self.status == 'issued':
            delta = self.due_date - date.today()
            return delta.days
        return 0
    
    def __repr__(self):
        return f'<Issue {self.id}: Book {self.book_id} to Member {self.member_id}>'


class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, available, completed, cancelled
    
    def __repr__(self):
        return f'<Reservation {self.id}>'
