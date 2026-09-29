"""
Issues routes — fully migrated to Firestore.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models.book import Book
from models.member import Member
from models.issue import Issue, Reservation
from models.fine import Fine
from models.setting import Setting
from routes.auth import login_required, admin_required
from routes.books import Pagination
from datetime import date, timedelta

issues_bp = Blueprint('issues', __name__, url_prefix='/issues')


@issues_bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    all_issues = Issue.search(query_text=search, status=status if status else None)
    # Sort newest first
    all_issues.sort(key=lambda i: i.issue_date or date.min, reverse=True)
    issues = Pagination(all_issues, page, per_page=15)
    today = date.today()

    return render_template('issues/index.html',
                           issues=issues, status=status, search=search, today=today)


@issues_bp.route('/issue', methods=['GET', 'POST'])
@admin_required
def issue_book():
    today = date.today()
    default_days = int(Setting.get('default_borrow_days', 14))
    max_books = int(Setting.get('max_books_per_member', 5))

    if request.method == 'POST':
        member_id = request.form.get('member_id', '').strip()
        book_id = request.form.get('book_id', '').strip()
        issue_date_str = request.form.get('issue_date')
        due_date_str = request.form.get('due_date')

        errors = []
        if not member_id: errors.append('Please select a member.')
        if not book_id: errors.append('Please select a book.')
        if not issue_date_str: errors.append('Issue date is required.')
        if not due_date_str: errors.append('Due date is required.')

        member = Member.get_by_id(member_id) if member_id else None
        book = Book.get_by_id(book_id) if book_id else None

        if member and member.status != 'active':
            errors.append(f'Member {member.name} is not active.')
        if book and book.available_copies <= 0:
            errors.append(f'Book "{book.title}" is not available.')
        if member and member.active_issues_count >= max_books:
            errors.append(f'Member has reached the maximum book limit ({max_books}).')
        if member and book:
            existing = Issue.get_by_member(member.id, status='issued')
            if any(i.book_id == book.id for i in existing):
                errors.append('This member already has this book issued.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('issues/issue.html', today=today, default_days=default_days)

        issue_date = date.fromisoformat(issue_date_str)
        due_date = date.fromisoformat(due_date_str)

        issue = Issue(
            book_id=book_id,
            member_id=member_id,
            issued_by=session.get('user_id', ''),
            issue_date=issue_date,
            due_date=due_date,
            status='issued',
        )
        issue.save()

        # Decrement available copies
        book.update(available_copies=book.available_copies - 1)

        # Complete any pending reservation
        reservations = Reservation.get_by_book(book_id, status='pending')
        for r in reservations:
            if r.member_id == member_id:
                r.update(status='completed')
                break

        flash(f'Book "{book.title}" issued to {member.name} successfully!', 'success')
        return redirect(url_for('issues.index'))

    return render_template('issues/issue.html', today=today, default_days=default_days)


@issues_bp.route('/return', methods=['GET', 'POST'])
@admin_required
def return_book():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    today = date.today()
    fine_per_day = float(Setting.get('fine_per_day', 5))

    if request.method == 'POST':
        issue_id = request.form.get('issue_id', '').strip()
        return_date_str = request.form.get('return_date')

        issue = Issue.get_by_id(issue_id)
        if not issue:
            flash('Issue record not found.', 'danger')
            return redirect(url_for('issues.return_book'))

        return_date = date.fromisoformat(return_date_str) if return_date_str else today
        fine_amount = 0.0

        if issue.due_date and return_date > issue.due_date:
            overdue_days = (return_date - issue.due_date).days
            fine_amount = overdue_days * fine_per_day

            fine = Fine(
                issue_id=issue.id,
                member_id=issue.member_id,
                amount=fine_amount,
                reason=f'Overdue return by {overdue_days} day(s)',
            )
            fine.save()

        issue.update(return_date=return_date, status='returned', fine_amount=fine_amount)

        # Restore available copy
        book = Book.get_by_id(issue.book_id)
        if book:
            book.update(available_copies=book.available_copies + 1)

        # Notify next reservation in queue
        next_reservations = Reservation.get_by_book(issue.book_id, status='pending')
        if next_reservations:
            next_reservations[0].update(status='available')

        if fine_amount > 0:
            flash(f'Book returned. Fine of ₹{fine_amount:.2f} has been applied.', 'warning')
        else:
            flash('Book returned successfully. No fine applicable.', 'success')
        return redirect(url_for('issues.return_book'))

    all_active = Issue.search(query_text=search, status='issued')
    all_active.sort(key=lambda i: i.due_date or date.min)
    active_issues = Pagination(all_active, page, per_page=15)

    return render_template('issues/return.html',
                           active_issues=active_issues, today=today, search=search)
