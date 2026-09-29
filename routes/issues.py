from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models import db
from models.book import Book
from models.member import Member
from models.issue import Issue, Reservation
from models.fine import Fine
from models.setting import Setting
from routes.auth import login_required, admin_required
from datetime import date, timedelta

issues_bp = Blueprint('issues', __name__, url_prefix='/issues')

@issues_bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    
    query = Issue.query
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.join(Member).join(Book).filter(
            (Member.name.ilike(f'%{search}%')) |
            (Book.title.ilike(f'%{search}%')) |
            (Member.member_id.ilike(f'%{search}%'))
        )
    
    issues = query.order_by(Issue.id.desc()).paginate(page=page, per_page=15, error_out=False)
    today = date.today()
    
    return render_template('issues/index.html', issues=issues, status=status, search=search, today=today)

@issues_bp.route('/issue', methods=['GET', 'POST'])
@admin_required
def issue_book():
    today = date.today()
    default_days = int(Setting.get('default_borrow_days', 14))
    max_books = int(Setting.get('max_books_per_member', 5))
    
    if request.method == 'POST':
        member_id = request.form.get('member_id', type=int)
        book_id = request.form.get('book_id', type=int)
        issue_date_str = request.form.get('issue_date')
        due_date_str = request.form.get('due_date')
        
        errors = []
        if not member_id: errors.append('Please select a member.')
        if not book_id: errors.append('Please select a book.')
        if not issue_date_str: errors.append('Issue date is required.')
        if not due_date_str: errors.append('Due date is required.')
        
        member = Member.query.get(member_id) if member_id else None
        book = Book.query.get(book_id) if book_id else None
        
        if member and member.status != 'active':
            errors.append(f'Member {member.name} is not active.')
        
        if book and book.available_copies <= 0:
            errors.append(f'Book "{book.title}" is not available.')
        
        if member and member.active_issues_count >= max_books:
            errors.append(f'Member has reached the maximum book limit ({max_books}).')
        
        if member and book:
            existing = Issue.query.filter_by(member_id=member.id, book_id=book.id, status='issued').first()
            if existing:
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
            issued_by=session['user_id'],
            issue_date=issue_date,
            due_date=due_date,
            status='issued'
        )
        book.available_copies -= 1
        
        # Check if there was a reservation and complete it
        reservation = Reservation.query.filter_by(
            book_id=book_id, member_id=member_id, status='pending'
        ).first()
        if reservation:
            reservation.status = 'completed'
        
        db.session.add(issue)
        db.session.commit()
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
        issue_id = request.form.get('issue_id', type=int)
        return_date_str = request.form.get('return_date')
        
        issue = Issue.query.get_or_404(issue_id)
        return_date = date.fromisoformat(return_date_str) if return_date_str else today
        
        issue.return_date = return_date
        issue.status = 'returned'
        issue.book.available_copies += 1
        
        # Calculate fine
        fine_amount = 0
        if return_date > issue.due_date:
            overdue_days = (return_date - issue.due_date).days
            fine_amount = overdue_days * fine_per_day
            issue.fine_amount = fine_amount
            
            fine = Fine(
                issue_id=issue.id,
                member_id=issue.member_id,
                amount=fine_amount,
                reason=f'Overdue return by {overdue_days} day(s)'
            )
            db.session.add(fine)
        
        # Check if any pending reservation for this book
        next_reservation = Reservation.query.filter_by(
            book_id=issue.book_id, status='pending'
        ).order_by(Reservation.reservation_date.asc()).first()
        if next_reservation:
            next_reservation.status = 'available'
        
        db.session.commit()
        
        if fine_amount > 0:
            flash(f'Book returned. Fine of ₹{fine_amount:.2f} has been applied.', 'warning')
        else:
            flash('Book returned successfully. No fine applicable.', 'success')
        
        return redirect(url_for('issues.return_book'))
    
    query = Issue.query.filter_by(status='issued')
    if search:
        query = query.join(Member).join(Book).filter(
            (Member.name.ilike(f'%{search}%')) |
            (Book.title.ilike(f'%{search}%')) |
            (Member.member_id.ilike(f'%{search}%'))
        )
    
    active_issues = query.order_by(Issue.due_date.asc()).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('issues/return.html', active_issues=active_issues, today=today, search=search)
