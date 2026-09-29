from . import db
from datetime import datetime

class Member(db.Model):
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    course = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    address = db.Column(db.Text)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    
    # Relationships
    issues = db.relationship('Issue', backref='member', lazy='dynamic', foreign_keys='Issue.member_id')
    reservations = db.relationship('Reservation', backref='member', lazy='dynamic')
    fines = db.relationship('Fine', backref='member', lazy='dynamic')
    user = db.relationship('User', backref='member_profile', foreign_keys=[user_id])
    
    @property
    def active_issues_count(self):
        return self.issues.filter_by(status='issued').count()
    
    @property
    def total_fines(self):
        return sum(f.amount for f in self.fines.filter_by(status='pending').all())
    
    def __repr__(self):
        return f'<Member {self.member_id}: {self.name}>'
