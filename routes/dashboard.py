from flask import Blueprint, render_template, session, jsonify
from models import db
from models.book import Book
from models.member import Member
from models.issue import Issue, Reservation
from models.fine import Fine
from models.user import User
from routes.auth import login_required, get_current_user
from datetime import date, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    user = get_current_user()
    
    if user.role == 'admin':
        return admin_dashboard(user)
    else:
        return member_dashboard(user)

def admin_dashboard(user):
    today = date.today()
    
    # Statistics
    total_books = Book.query.count()
    available_books = db.session.query(func.sum(Book.available_copies)).scalar() or 0
    issued_books = Issue.query.filter_by(status='issued').count()
    total_members = Member.query.count()
    overdue_books = Issue.query.filter(
        Issue.status == 'issued',
        Issue.due_date < today
    ).count()
    pending_fines = db.session.query(func.sum(Fine.amount)).filter_by(status='pending').scalar() or 0
    
    # Recent activities (last 10)
    recent_issues = Issue.query.order_by(Issue.id.desc()).limit(10).all()
    
    # Overdue issues
    overdue_issues = Issue.query.filter(
        Issue.status == 'issued',
        Issue.due_date < today
    ).order_by(Issue.due_date.asc()).limit(5).all()
    
    # Chart data: Issues per day for last 30 days
    thirty_days_ago = today - timedelta(days=30)
    daily_issues_query = db.session.query(
        Issue.issue_date,
        func.count(Issue.id).label('count')
    ).filter(Issue.issue_date >= thirty_days_ago).group_by(Issue.issue_date).all()
    daily_issues = [[str(r[0]), r[1]] for r in daily_issues_query]
    
    # Books by category
    category_stats_query = db.session.query(
        Book.category,
        func.count(Book.id).label('count')
    ).group_by(Book.category).all()
    category_stats = [[r[0], r[1]] for r in category_stats_query]
    
    # Monthly returns (last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_returns_query = db.session.query(
        func.strftime('%Y-%m', Issue.return_date).label('month'),
        func.count(Issue.id).label('count')
    ).filter(
        Issue.return_date >= six_months_ago,
        Issue.status == 'returned'
    ).group_by(func.strftime('%Y-%m', Issue.return_date)).all()
    monthly_returns = [[r[0], r[1]] for r in monthly_returns_query]
    
    # Monthly fine collection
    monthly_fines_query = db.session.query(
        func.strftime('%Y-%m', Fine.paid_date).label('month'),
        func.sum(Fine.amount).label('total')
    ).filter(
        Fine.status == 'paid',
        Fine.paid_date >= six_months_ago
    ).group_by(func.strftime('%Y-%m', Fine.paid_date)).all()
    monthly_fines = [[r[0], float(r[1]) if r[1] else 0] for r in monthly_fines_query]
    
    return render_template('dashboard.html',
        user=user,
        total_books=total_books,
        available_books=int(available_books),
        issued_books=issued_books,
        total_members=total_members,
        overdue_books=overdue_books,
        pending_fines=pending_fines,
        recent_issues=recent_issues,
        overdue_issues=overdue_issues,
        daily_issues=daily_issues,
        category_stats=category_stats,
        monthly_returns=monthly_returns,
        monthly_fines=monthly_fines
    )

def member_dashboard(user):
    member = Member.query.filter_by(email=user.email).first()
    today = date.today()
    
    if not member:
        current_issues = []
        due_soon = []
        overdue = []
        history = []
        reservations = []
        outstanding_fines = 0
        popular_books = Book.query.filter(Book.available_copies > 0).limit(6).all()
        return render_template('member_dashboard.html',
            user=user, member=None,
            current_issues=current_issues,
            due_soon=due_soon,
            overdue=overdue,
            history=history,
            reservations=reservations,
            outstanding_fines=outstanding_fines,
            popular_books=popular_books
        )
    
    current_issues = Issue.query.filter_by(member_id=member.id, status='issued').all()
    due_soon = [i for i in current_issues if 0 <= i.days_remaining <= 3]
    overdue = [i for i in current_issues if i.is_overdue]
    history = Issue.query.filter_by(member_id=member.id, status='returned').order_by(Issue.return_date.desc()).limit(10).all()
    reservations = Reservation.query.filter_by(member_id=member.id).filter(
        Reservation.status.in_(['pending', 'available'])
    ).all()
    outstanding_fines = db.session.query(func.sum(Fine.amount)).filter_by(
        member_id=member.id, status='pending'
    ).scalar() or 0
    popular_books = Book.query.filter(Book.available_copies > 0).limit(6).all()
    
    return render_template('member_dashboard.html',
        user=user,
        member=member,
        current_issues=current_issues,
        due_soon=due_soon,
        overdue=overdue,
        history=history,
        reservations=reservations,
        outstanding_fines=outstanding_fines,
        popular_books=popular_books
    )
