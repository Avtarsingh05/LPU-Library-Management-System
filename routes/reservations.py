"""
Reservations routes — fully migrated to Firestore.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models.book import Book
from models.member import Member
from models.issue import Reservation
from routes.auth import login_required, admin_required
from routes.books import Pagination

reservations_bp = Blueprint('reservations', __name__, url_prefix='/reservations')


@reservations_bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    all_res = Reservation.get_all(status=status if status else None)
    reservations = Pagination(all_res, page, per_page=15)
    return render_template('reservations/index.html', reservations=reservations, status=status)


@reservations_bp.route('/create', methods=['POST'])
@login_required
def create():
    book_id = request.form.get('book_id', '').strip()
    book = Book.get_by_id(book_id)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books.index'))

    member = Member.get_by_email(session.get('user_email', ''))
    if not member:
        flash('Member profile not found.', 'danger')
        return redirect(url_for('books.view', id=book_id))

    if Reservation.get_active_for_member_book(book_id, member.id):
        flash('You already have an active reservation for this book.', 'warning')
        return redirect(url_for('books.view', id=book_id))

    reservation = Reservation(book_id=book_id, member_id=member.id)
    reservation.save()
    flash(f'Reservation for "{book.title}" created successfully!', 'success')
    return redirect(url_for('books.view', id=book_id))


@reservations_bp.route('/<id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    reservation = Reservation.get_by_id(id)
    if not reservation:
        flash('Reservation not found.', 'danger')
        return redirect(url_for('dashboard.index'))

    if session.get('user_role') != 'admin':
        member = Member.get_by_email(session.get('user_email', ''))
        if not member or reservation.member_id != member.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard.index'))

    reservation.update(status='cancelled')
    flash('Reservation cancelled successfully.', 'info')
    if session.get('user_role') == 'admin':
        return redirect(url_for('reservations.index'))
    return redirect(url_for('dashboard.index'))
