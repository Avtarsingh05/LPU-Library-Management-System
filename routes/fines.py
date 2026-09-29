"""
Fines routes — fully migrated to Firestore.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from models.fine import Fine
from routes.auth import admin_required
from routes.books import Pagination
from datetime import datetime

fines_bp = Blueprint('fines', __name__, url_prefix='/fines')


@fines_bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    all_fines = Fine.search(query_text=search, status=status)
    fines = Pagination(all_fines, page, per_page=15)

    total_pending = Fine.total_amount('pending')
    total_collected = Fine.total_amount('paid')

    return render_template('fines/index.html',
        fines=fines, status=status, search=search,
        total_pending=total_pending, total_collected=total_collected)


@fines_bp.route('/<id>/mark-paid', methods=['POST'])
@admin_required
def mark_paid(id):
    fine = Fine.get_by_id(id)
    if not fine:
        flash('Fine not found.', 'danger')
        return redirect(url_for('fines.index'))
    fine.update(status='paid', paid_date=datetime.utcnow())
    flash(f'Fine of ₹{fine.amount:.2f} marked as paid.', 'success')
    return redirect(url_for('fines.index'))


@fines_bp.route('/<id>/waive', methods=['POST'])
@admin_required
def waive(id):
    fine = Fine.get_by_id(id)
    if not fine:
        flash('Fine not found.', 'danger')
        return redirect(url_for('fines.index'))
    fine.update(status='waived', paid_date=datetime.utcnow())
    flash(f'Fine of ₹{fine.amount:.2f} has been waived.', 'info')
    return redirect(url_for('fines.index'))
