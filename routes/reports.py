"""
Reports routes — fully migrated to Firestore.
"""
from flask import Blueprint, render_template, request, make_response
from models.book import Book
from models.member import Member
from models.issue import Issue
from models.fine import Fine
from routes.auth import admin_required
from datetime import date, timedelta, datetime
from collections import Counter
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
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:  # month
        start_date = today - timedelta(days=30)

    all_issues = Issue.get_all()
    all_fines = Fine.get_all()
    all_books = Book.get_all()

    # Filter issues by period
    period_issues = [i for i in all_issues
                     if i.issue_date and i.issue_date >= start_date]

    # Most borrowed books in period
    book_counts = Counter(i.book_id for i in period_issues)
    book_map = {b.id: b for b in all_books}
    most_borrowed = []
    for bid, cnt in book_counts.most_common(10):
        b = book_map.get(bid)
        if b:
            most_borrowed.append((b.title, b.author, cnt))

    # Most active members in period
    member_counts = Counter(i.member_id for i in period_issues)
    member_map = {m.id: m for m in Member.get_all()}
    most_active = []
    for mid, cnt in member_counts.most_common(10):
        m = member_map.get(mid)
        if m:
            most_active.append((m.name, m.member_id, cnt))

    # Overdue issues
    overdue_issues = Issue.get_overdue()

    # Summary stats
    total_issued = len(period_issues)
    total_returned = len([i for i in period_issues
                          if i.status == 'returned' and i.return_date and i.return_date >= start_date])
    fine_collected = sum(f.amount for f in all_fines
                         if f.status == 'paid' and f.paid_date and
                         _dt_to_date(f.paid_date) >= start_date)

    # Category stats
    cat_data = {}
    for b in all_books:
        if b.category not in cat_data:
            cat_data[b.category] = {'book_count': 0, 'total_copies': 0, 'available_copies': 0}
        cat_data[b.category]['book_count'] += 1
        cat_data[b.category]['total_copies'] += b.total_copies
        cat_data[b.category]['available_copies'] += b.available_copies
    category_stats = [(cat, v['book_count'], v['total_copies'], v['available_copies'])
                      for cat, v in cat_data.items()]

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
        category_stats=category_stats,
    )


def _dt_to_date(val):
    if isinstance(val, date):
        return val
    if hasattr(val, 'date'):
        return val.date()
    return date.min


@reports_bp.route('/export/issued')
@admin_required
def export_issued():
    period = request.args.get('period', 'month')
    today = date.today()
    start_date = today - timedelta(days=30 if period == 'month' else 365)

    issues = [i for i in Issue.get_all() if i.issue_date and i.issue_date >= start_date]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Issue ID', 'Book Title', 'Book ISBN', 'Member Name', 'Member ID',
                     'Issue Date', 'Due Date', 'Return Date', 'Status', 'Fine Amount'])
    for i in issues:
        b = i.book
        m = i.member
        writer.writerow([
            i.id,
            b.title if b else '',
            b.isbn if b else '',
            m.name if m else '',
            m.member_id if m else '',
            i.issue_date,
            i.due_date,
            i.return_date or '',
            i.status,
            i.fine_amount,
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=issued_books_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@reports_bp.route('/export/fines')
@admin_required
def export_fines():
    fines = Fine.get_all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fine ID', 'Member Name', 'Member ID', 'Book Title', 'Amount',
                     'Reason', 'Status', 'Created At', 'Paid Date'])
    for f in fines:
        m = f.member
        iss = f.issue
        writer.writerow([
            f.id,
            m.name if m else '',
            m.member_id if m else '',
            iss.book.title if iss and iss.book else '',
            f.amount,
            f.reason,
            f.status,
            f.created_at,
            f.paid_date or '',
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=fines_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response
