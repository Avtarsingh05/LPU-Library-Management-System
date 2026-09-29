from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models import db
from models.book import Book
from models.member import Member
from models.issue import Issue, Reservation
from routes.auth import login_required, admin_required

reservations_bp = Blueprint('reservations', __name__, url_prefix='/reservations')

@reservations_bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Reservation.query
    if status:
        query = query.filter_by(status=status)
    
    reservations = query.order_by(Reservation.reservation_date.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('reservations/index.html', reservations=reservations, status=status)

@reservations_bp.route('/create', methods=['POST'])
@login_required
def create():
    book_id = request.form.get('book_id', type=int)
    book = Book.query.get_or_404(book_id)
    
    member = Member.query.filter_by(email=session.get('user_email')).first()
    if not member:
        flash('Member profile not found.', 'danger')
        return redirect(url_for('books.view', id=book_id))
    
    existing = Reservation.query.filter_by(
        book_id=book_id, member_id=member.id
    ).filter(Reservation.status.in_(['pending', 'available'])).first()
    
    if existing:
        flash('You already have an active reservation for this book.', 'warning')
        return redirect(url_for('books.view', id=book_id))
    
    reservation = Reservation(book_id=book_id, member_id=member.id)
    db.session.add(reservation)
    db.session.commit()
    flash(f'Reservation for "{book.title}" created successfully!', 'success')
    return redirect(url_for('books.view', id=book_id))

@reservations_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    reservation = Reservation.query.get_or_404(id)
    
    if session.get('user_role') != 'admin':
        member = Member.query.filter_by(email=session.get('user_email')).first()
        if not member or reservation.member_id != member.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard.index'))
    
    reservation.status = 'cancelled'
    db.session.commit()
    flash('Reservation cancelled successfully.', 'info')
    return redirect(url_for('reservations.index') if session.get('user_role') == 'admin' else url_for('dashboard.index'))
