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
from routes.auth import login_required
import requests as req
import hmac
import hashlib
from flask import current_app, jsonify, session
from models.member import Member

@fines_bp.route('/create_order', methods=['POST'])
@login_required
def create_order():
    try:
        user_email = session.get('user_email')
        member = Member.get_by_email(user_email)
        if not member:
            return jsonify({'error': 'Member not found'}), 404
            
        pending_fines = Fine.get_by_member(member.id, status='pending')
        total_amount = sum(f.amount for f in pending_fines)
        
        if total_amount <= 0:
            return jsonify({'error': 'No pending fines'}), 400
            
        key_id = current_app.config.get('RAZORPAY_KEY_ID')
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
        
        if not key_id or not key_secret or 'your_' in key_id:
            return jsonify({
                'id': 'order_dummy_123',
                'amount': int(total_amount * 100),
                'currency': 'INR',
                'dummy': True
            })
            
        auth = (key_id, key_secret)
        data = { "amount": int(total_amount * 100), "currency": "INR", "receipt": f"receipt_{member.id}" }
        
        r = req.post("https://api.razorpay.com/v1/orders", json=data, auth=auth, timeout=10)
        if r.status_code != 200:
            return jsonify({'error': f'Razorpay API error: {r.text}'}), 400
            
        payment = r.json()
        return jsonify({
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'key': key_id,
            'dummy': False
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@fines_bp.route('/verify_payment', methods=['POST'])
@login_required
def verify_payment():
    try:
        data = request.json
        user_email = session.get('user_email')
        member = Member.get_by_email(user_email)
        
        key_id = current_app.config.get('RAZORPAY_KEY_ID')
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
        
        if data.get('dummy') and (not key_id or not key_secret or 'your_' in key_id):
            pending_fines = Fine.get_by_member(member.id, status='pending')
            for f in pending_fines:
                f.update(status='paid', paid_date=datetime.utcnow())
                if f.issue_id:
                    from models.issue import Issue
                    issue = Issue.get_by_id(f.issue_id)
                    if issue:
                        issue.update(fine_amount=0)
            return jsonify({'status': 'success'})
        elif data.get('dummy'):
            return jsonify({'status': 'failed', 'error': 'Dummy payments are disabled in production'}), 403
            
        order_id = data.get('razorpay_order_id', '')
        payment_id = data.get('razorpay_payment_id', '')
        signature = data.get('razorpay_signature', '')
        
        msg = f"{order_id}|{payment_id}"
        generated_sig = hmac.new(key_secret.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(generated_sig, signature):
            return jsonify({'status': 'failed', 'error': 'Invalid payment signature'}), 400
        
        pending_fines = Fine.get_by_member(member.id, status='pending')
        for f in pending_fines:
            f.update(status='paid', paid_date=datetime.utcnow())
            if f.issue_id:
                from models.issue import Issue
                issue = Issue.get_by_id(f.issue_id)
                if issue:
                    issue.update(fine_amount=0)
                    
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'failed', 'error': str(e)}), 400


