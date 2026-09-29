from . import db
from datetime import datetime

class Fine(db.Model):
    __tablename__ = 'fines'
    
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issues.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(200), default='Overdue return')
    status = db.Column(db.String(20), default='pending')  # pending, paid, waived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_date = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Fine {self.id}: ₹{self.amount}>'
