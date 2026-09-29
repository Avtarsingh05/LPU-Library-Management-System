from flask import Blueprint, render_template, request, make_response
from models import db
from models.book import Book
from models.member import Member
from models.issue import Issue
from models.fine import Fine
from routes.auth import admin_required
from datetime import date, timedelta, datetime
from sqlalchemy import func
import csv
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@admin_required
def index():
    period = request.args.get('period', 'month')
    today = date.today()
    
    if period == 'today':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    # Most borrowed books
    most_borrowed = db.session.query(
        Book.title, Book.author, func.count(Issue.id).label('borrow_count')
    ).join(Issue, Issue.book_id == Book.id).filter(
        Issue.issue_date >= start_date
    ).group_by(Book.id).order_by(func.count(Issue.id).desc()).limit(10).all()
    
    # Most active members
    most_active = db.session.query(
        Member.name, Member.member_id, func.count(Issue.id).label('issue_count')
    ).join(Issue, Issue.member_id == Member.id).filter(
        Issue.issue_date >= start_date
    ).group_by(Member.id).order_by(func.count(Issue.id).desc()).limit(10).all()
    
    # Overdue books
    overdue_issues = Issue.query.filter(
        Issue.status == 'issued',
        Issue.due_date < today
    ).order_by(Issue.due_date.asc()).all()
    
    # Summary stats
    total_issued = Issue.query.filter(Issue.issue_date >= start_date).count()
    total_returned = Issue.query.filter(
        Issue.status == 'returned',
        Issue.return_date >= start_date
    ).count()
    fine_collected = db.session.query(func.sum(Fine.amount)).filter(
        Fine.status == 'paid',
        Fine.paid_date >= datetime.combine(start_date, datetime.min.time())
    ).scalar() or 0
    
    # Category statistics
    category_stats = db.session.query(
        Book.category,
        func.count(Book.id).label('book_count'),
        func.sum(Book.total_copies).label('total_copies'),
        func.sum(Book.available_copies).label('available_copies')
    ).group_by(Book.category).all()
    
    return render_template('reports/index.html',
        period=period,
        start_date=start_date,
        today=today,
        most_borrowed=most_borrowed,
        most_active=most_active,
        overdue_issues=overdue_issues,
        total_issued=total_issued,
        total_returned=total_returned,
        fine_collected=fine_collected,
        category_stats=category_stats
    )

@reports_bp.route('/export/issued')
@admin_required
def export_issued():
    period = request.args.get('period', 'month')
    today = date.today()
    start_date = today - timedelta(days=30) if period == 'month' else today - timedelta(days=365)
    
    issues = Issue.query.filter(Issue.issue_date >= start_date).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Issue ID', 'Book Title', 'Book ISBN', 'Member Name', 'Member ID',
                     'Issue Date', 'Due Date', 'Return Date', 'Status', 'Fine Amount'])
    
    for issue in issues:
        writer.writerow([
            issue.id,
            issue.book.title,
            issue.book.isbn,
            issue.member.name,
            issue.member.member_id,
            issue.issue_date,
            issue.due_date,
            issue.return_date or '',
            issue.status,
            issue.fine_amount
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=issued_books_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@reports_bp.route('/export/fines')
@admin_required
def export_fines():
    fines = Fine.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fine ID', 'Member Name', 'Member ID', 'Book Title', 'Amount',
                     'Reason', 'Status', 'Created At', 'Paid Date'])
    
    for fine in fines:
        writer.writerow([
            fine.id,
            fine.member.name,
            fine.member.member_id,
            fine.issue.book.title,
            fine.amount,
            fine.reason,
            fine.status,
            fine.created_at,
            fine.paid_date or ''
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=fines_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response
