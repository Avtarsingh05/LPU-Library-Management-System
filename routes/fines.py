from flask import Blueprint, render_template, redirect, url_for, request, flash
from models import db
from models.fine import Fine
from models.member import Member
from routes.auth import login_required, admin_required
from datetime import datetime
from sqlalchemy import func

fines_bp = Blueprint('fines', __name__, url_prefix='/fines')

@fines_bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    
    query = Fine.query
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.join(Member).filter(
            (Member.name.ilike(f'%{search}%')) |
            (Member.member_id.ilike(f'%{search}%'))
        )
    
    fines = query.order_by(Fine.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    
    total_pending = db.session.query(func.sum(Fine.amount)).filter_by(status='pending').scalar() or 0
    total_collected = db.session.query(func.sum(Fine.amount)).filter_by(status='paid').scalar() or 0
    
    return render_template('fines/index.html',
        fines=fines, status=status, search=search,
        total_pending=total_pending, total_collected=total_collected
    )

@fines_bp.route('/<int:id>/mark-paid', methods=['POST'])
@admin_required
def mark_paid(id):
    fine = Fine.query.get_or_404(id)
    fine.status = 'paid'
    fine.paid_date = datetime.utcnow()
    db.session.commit()
    flash(f'Fine of ₹{fine.amount:.2f} marked as paid.', 'success')
    return redirect(url_for('fines.index'))

@fines_bp.route('/<int:id>/waive', methods=['POST'])
@admin_required
def waive(id):
    fine = Fine.query.get_or_404(id)
    fine.status = 'waived'
    fine.paid_date = datetime.utcnow()
    db.session.commit()
    flash(f'Fine of ₹{fine.amount:.2f} has been waived.', 'info')
    return redirect(url_for('fines.index'))
