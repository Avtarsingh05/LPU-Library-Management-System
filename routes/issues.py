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
    issues = Pagination(all_issues, page, per_page=10)
    today = date.today()
    
    # Preload library names
    from models.library import Library
    libraries = {lib.id: lib for lib in Library.get_all()}
    for issue in issues.items:
        if issue.library_id and issue.library_id in libraries:
            issue.library_name = libraries[issue.library_id].name
        else:
            issue.library_name = "Global / Unknown"

    return render_template('issues/index.html',
                           issues=issues, status=status, search=search, today=today)

@issues_bp.route('/<id>/delete', methods=['POST'])
@admin_required
def delete(id):
    from models.user import User
    current_user = User.get_by_id(session.get('user_id'))
    if not current_user.is_super_admin():
        flash('Only Super Admins can delete issue records.', 'danger')
        return redirect(url_for('issues.index'))
        
    issue = Issue.get_by_id(id)
    if not issue:
        flash('Issue not found.', 'danger')
        return redirect(url_for('issues.index'))
        
    # We should restore the book copy availability if it's currently issued
    if issue.status == 'issued':
        book = Book.get_by_id(issue.book_id)
        if book:
            book.update(available_copies=book.available_copies + 1)
        if issue.copy_id:
            from models.book_copy import BookCopy
            copy = BookCopy.get_by_id(issue.copy_id)
            if copy:
                copy.update(status='AVAILABLE')
                
    db = get_db()
    db.collection('issues').document(id).delete()
    flash('Issue record deleted successfully.', 'success')
    return redirect(url_for('issues.index'))


from firebase_admin import firestore
from models import get_db

@issues_bp.route('/issue', methods=['GET', 'POST'])
@admin_required
def issue_book():
    today = date.today()
    default_days = int(Setting.get('default_borrow_days', 14))
    max_books = int(Setting.get('max_books_per_member', 5))

    if request.method == 'POST':
        member_id = request.form.get('member_id', '').strip()
        copy_id = request.form.get('copy_id', '').strip()
        book_id = request.form.get('book_id', '').strip() # Fallback for backward compat
        issue_date_str = request.form.get('issue_date')
        due_date_str = request.form.get('due_date')

        if not member_id: flash('Please select a member.', 'danger'); return redirect(url_for('issues.issue_book'))
        if not copy_id and not book_id: flash('Please provide a Book ID or Copy ID.', 'danger'); return redirect(url_for('issues.issue_book'))

        member = Member.get_by_id(member_id)
        if not member or member.status != 'active':
            flash('Invalid or inactive member.', 'danger')
            return redirect(url_for('issues.issue_book'))

        if member.verification_status != 'approved':
            flash('Member ID verification is not approved.', 'danger')
            return redirect(url_for('issues.issue_book'))

        if member.active_issues_count >= max_books:
            flash(f'Member has reached the maximum book limit ({max_books}).', 'danger')
            return redirect(url_for('issues.issue_book'))

        # Fetch copy if copy_id is provided
        from models.book_copy import BookCopy
        from models.user import User
        
        current_user = User.get_by_id(session.get('user_id'))
        
        copy = None
        if copy_id:
            copy = BookCopy.get_by_id(copy_id)
            if not copy:
                flash('Physical copy not found.', 'danger')
                return redirect(url_for('issues.issue_book'))
            book_id = copy.book_id
            
        book = Book.get_by_id(book_id)
        if not book:
            flash('Book not found.', 'danger')
            return redirect(url_for('issues.issue_book'))

        # Check existing issues for the book
        existing = Issue.get_by_member(member.id, status='issued')
        if any(i.book_id == book.id for i in existing):
            flash('This member already has this book issued.', 'danger')
            return redirect(url_for('issues.issue_book'))

        # AUTHORIZATION ENFORCEMENT
        target_library_id = copy.library_id if copy else None
        
        if current_user.role == 'librarian':
            assigned_libs = current_user.get_assigned_library_ids()
            if not assigned_libs:
                flash('No library assigned. Contact Super Admin.', 'danger')
                return redirect(url_for('issues.issue_book'))
            
            if copy:
                if copy.library_id not in assigned_libs:
                    flash('You are not authorized to issue books from this library.', 'danger')
                    return redirect(url_for('issues.issue_book'))
            else:
                flash('Librarians must issue books using a specific physical copy ID from their library.', 'danger')
                return redirect(url_for('issues.issue_book'))
                
        # ATOMIC TRANSACTION
        db = get_db()
        transaction = db.transaction()
        
        @firestore.transactional
        def process_issue(transaction):
            if copy:
                copy_ref = db.collection('book_copies').document(copy.id)
                copy_snap = copy_ref.get(transaction=transaction)
                if not copy_snap.exists or copy_snap.get('status') != 'AVAILABLE':
                    return False, "This physical copy is not available."
                    
            book_ref = db.collection('books').document(book.id)
            book_snap = book_ref.get(transaction=transaction)
            if not book_snap.exists or book_snap.get('available_copies') <= 0:
                return False, "No available copies for this book."
            
            # Update copy
            if copy:
                transaction.update(copy_ref, {'status': 'ISSUED', 'updated_at': firestore.SERVER_TIMESTAMP})
            
            # Update book availability
            transaction.update(book_ref, {'available_copies': book_snap.get('available_copies') - 1})
            
            # Create issue document
            issue_ref = db.collection('issues').document()
            issue_data = {
                'book_id': book.id,
                'copy_id': copy.id if copy else None,
                'library_id': copy.library_id if copy else None,
                'member_id': member.id,
                'issued_by': current_user.id,
                'issue_date': date.fromisoformat(issue_date_str).isoformat(),
                'due_date': date.fromisoformat(due_date_str).isoformat(),
                'status': 'issued',
                'fine_amount': 0,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            transaction.set(issue_ref, issue_data)
            return True, issue_ref.id

        success, result = process_issue(transaction)
        
        if not success:
            flash(result, 'danger')
            return redirect(url_for('issues.issue_book'))
            
        new_issue_id = result
            
        # Audit log
        from models.audit_log import AuditLog
        AuditLog(
            actor_id=current_user.id,
            actor_role=current_user.role,
            library_id=target_library_id,
            action='ISSUE_BOOK',
            entity_type='Issue',
            entity_id=new_issue_id,
            metadata={'book_id': book.id, 'member_id': member.id, 'copy_id': copy.id if copy else None}
        ).save()

        # Complete any pending reservation
        reservations = Reservation.get_by_book(book.id, status='pending')
        for r in reservations:
            if r.member_id == member.id:
                r.update(status='completed')
                break

        flash(f'Book "{book.title}" issued to {member.name} successfully!', 'success')
        return redirect(url_for('issues.index'))

    # Fetch assigned libraries
    from models.user import User
    from models.library import Library
    current_user = User.get_by_id(session.get('user_id'))
    assigned_libraries = []
    
    if current_user.role == 'super_admin' or current_user.role == 'admin':
        assigned_libraries = Library.get_all()
    else:
        assigned_lib_ids = current_user.get_assigned_library_ids()
        for lid in assigned_lib_ids:
            lib = Library.get_by_id(lid)
            if lib: assigned_libraries.append(lib)

    return render_template('issues/issue.html', today=today, default_days=default_days, assigned_libraries=assigned_libraries)


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

        # AUTHORIZATION ENFORCEMENT
        from models.user import User
        current_user = User.get_by_id(session.get('user_id'))
        if current_user.role == 'librarian':
            assigned_libs = current_user.get_assigned_library_ids()
            if not assigned_libs:
                flash('No library assigned. Contact Super Admin.', 'danger')
                return redirect(url_for('issues.return_book'))
            
            if issue.library_id and issue.library_id not in assigned_libs:
                flash('You are not authorized to return books for this library.', 'danger')
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

        condition = request.form.get('condition', 'GOOD')
        condition_notes = request.form.get('condition_notes', '')

        # ATOMIC TRANSACTION FOR RETURN
        db = get_db()
        transaction = db.transaction()
        
        @firestore.transactional
        def process_return(transaction):
            issue_ref = db.collection('issues').document(issue.id)
            issue_snap = issue_ref.get(transaction=transaction)
            if not issue_snap.exists or issue_snap.get('status') == 'returned':
                return False, "Issue already returned or not found."
                
            book_ref = db.collection('books').document(issue.book_id)
            book_snap = book_ref.get(transaction=transaction)
            
            copy_ref = None
            if issue.copy_id:
                copy_ref = db.collection('book_copies').document(issue.copy_id)
                copy_snap = copy_ref.get(transaction=transaction)

            # Update Issue
            transaction.update(issue_ref, {'return_date': return_date.isoformat(), 'status': 'returned', 'fine_amount': fine_amount})
            
            # Update Copy
            if copy_ref and copy_snap.exists:
                status_to_set = 'AVAILABLE'
                if condition in ['DAMAGED', 'LOST', 'UNDER_REPAIR']:
                    status_to_set = condition
                transaction.update(copy_ref, {'status': status_to_set, 'condition': condition, 'condition_notes': condition_notes})
            
            # Update Book availability if condition is good
            if book_snap.exists:
                if condition not in ['DAMAGED', 'LOST', 'UNDER_REPAIR']:
                    transaction.update(book_ref, {'available_copies': book_snap.get('available_copies') + 1})
                    
            return True, None

        success, error_msg = process_return(transaction)
        if not success:
            flash(error_msg, 'danger')
            return redirect(url_for('issues.return_book'))

        # Audit log
        from models.audit_log import AuditLog
        AuditLog(
            actor_id=current_user.id,
            actor_role=current_user.role,
            library_id=issue.library_id,
            action='RETURN_BOOK',
            entity_type='Issue',
            entity_id=issue.id,
            metadata={'book_id': issue.book_id, 'member_id': issue.member_id, 'copy_id': issue.copy_id, 'condition': condition, 'fine_amount': fine_amount}
        ).save()

        # Notify next reservation in queue
        next_reservations = Reservation.get_by_book(issue.book_id, status='pending')
        if next_reservations:
            # Check if reservation is for the same library if cross-library borrowing is restricted
            # For now, satisfy the first reservation queue
            next_res = next_reservations[0]
            next_res.update(status='available')
            
            from models.notification import Notification
            from models.member import Member
            book = Book.get_by_id(issue.book_id)
            member = Member.get_by_id(next_res.member_id)
            if member and book:
                Notification(
                    user_id=member.user_id,
                    title='Reservation Available',
                    message=f'The book "{book.title}" you reserved is now available.',
                    type='success'
                ).save()

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
