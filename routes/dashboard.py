"""
Dashboard routes — fully migrated to Firestore.
"""
from flask import Blueprint, render_template, session
from models.book import Book
from models.member import Member
from models.issue import Issue, Reservation
from models.fine import Fine
from models.user import User
from routes.auth import login_required, get_current_user
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    user = get_current_user()
    if not user:
        session.clear()
        return __import__('flask').redirect(__import__('flask').url_for('auth.login'))

    if user.is_admin() or user.is_librarian():
        return _admin_dashboard(user)
    else:
        return _member_dashboard(user)


def _admin_dashboard(user):
    today = date.today()
    today_str = today.isoformat()

    try:
        all_issues = Issue.get_all()
        all_fines = Fine.get_all(status='pending')
        
        # Super Admin vs Librarian Filtering
        if user.role == 'librarian':
            assigned_libs = user.get_assigned_library_ids()
            all_issues = [i for i in all_issues if i.library_id in assigned_libs]
            
            # Since Book covers all libraries, if a librarian manages a library, they only see stats for physical copies they manage.
            from models.book_copy import BookCopy
            all_copies = BookCopy.get_all()
            my_copies = [c for c in all_copies if c.library_id in assigned_libs]
            total_books = len(my_copies)
            available_books = sum(1 for c in my_copies if c.status == 'AVAILABLE')
        else:
            total_books = Book.count()
            available_books = Book.total_available()

        issued_books = sum(1 for i in all_issues if i.status == 'issued')
        total_members = Member.count()
        overdue_issues_list = [i for i in all_issues if i.status == 'issued' and i.is_overdue]
        overdue_books = len(overdue_issues_list)
        
        if user.role == 'librarian':
            # Fines are tied to issues. We can filter fines by checking if they relate to an issue in this library.
            issue_ids = {i.id for i in all_issues}
            all_fines = [f for f in all_fines if f.issue_id in issue_ids]
            
        pending_fines = sum(f.amount for f in all_fines)

        # Recent issues (last 10)
        recent_issues = sorted(all_issues, key=lambda i: i.issue_date or date.min, reverse=True)[:10]

        # Overdue (top 5)
        overdue_issues = overdue_issues_list[:5]

        # Chart: issues per day last 30 days
        thirty_days_ago = today - timedelta(days=30)
        daily_counts = {}
        for i in all_issues:
            if i.issue_date and i.issue_date >= thirty_days_ago:
                key = i.issue_date.isoformat()
                daily_counts[key] = daily_counts.get(key, 0) + 1
        daily_issues = [[k, v] for k, v in sorted(daily_counts.items())]

        # Category stats
        cat_counts = {}
        for b in Book.get_all():
            cat_counts[b.category] = cat_counts.get(b.category, 0) + 1
        category_stats = [[k, v] for k, v in cat_counts.items()]

        # Monthly returns last 6 months
        six_months_ago = today - timedelta(days=180)
        month_returns = {}
        for i in all_issues:
            if i.status == 'returned' and i.return_date and i.return_date >= six_months_ago:
                key = i.return_date.strftime('%Y-%m')
                month_returns[key] = month_returns.get(key, 0) + 1
        monthly_returns = [[k, v] for k, v in sorted(month_returns.items())]

        # Monthly fine collection
        paid_fines = Fine.get_all(status='paid')
        if user.role == 'librarian':
            paid_fines = [f for f in paid_fines if f.issue_id in issue_ids]
        month_fines = {}
        for f in paid_fines:
            if f.paid_date:
                try:
                    if hasattr(f.paid_date, 'strftime'):
                        key = f.paid_date.strftime('%Y-%m')
                    else:
                        key = str(f.paid_date)[:7]
                    month_fines[key] = month_fines.get(key, 0) + f.amount
                except Exception:
                    pass
        monthly_fines = [[k, v] for k, v in sorted(month_fines.items())]
        
        # Insights Generation
        insights = []
        if len(overdue_issues_list) > 5:
            insights.append(f"High number of overdue books ({len(overdue_issues_list)}). Consider sending reminders.")
        if pending_fines > 1000:
            insights.append(f"Significant pending fines (₹{pending_fines:.0f}).")
        
        popular_categories = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
        if popular_categories:
            insights.append(f"'{popular_categories[0][0]}' is your top category with {popular_categories[0][1]} books.")
            
        # Check demand (reservations)
        from models.issue import Reservation
        all_res = Reservation.get_all(status='pending')
        if all_res:
            res_by_book = {}
            for r in all_res:
                res_by_book[r.book_id] = res_by_book.get(r.book_id, 0) + 1
            if res_by_book:
                top_book_id = max(res_by_book, key=res_by_book.get)
                # If librarian, check if they manage this book's copies
                if user.role != 'librarian' or any(c.book_id == top_book_id for c in my_copies):
                    top_book = Book.get_by_id(top_book_id)
                    if top_book:
                        insights.append(f"'{top_book.title}' has {res_by_book[top_book_id]} active reservations. Consider purchasing additional copies.")

    except Exception as e:
        # Graceful fallback if Firestore isn't ready yet
        total_books = available_books = issued_books = total_members = 0
        overdue_books = pending_fines = 0
        recent_issues = overdue_issues = []
        daily_issues = category_stats = monthly_returns = monthly_fines = []
        insights = []

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
        monthly_fines=monthly_fines,
        insights=insights
    )


def _member_dashboard(user):
    today = date.today()
    try:
        member = Member.get_by_email(user.email)
        if not member:
            popular_books = [b for b in Book.get_all() if b.available_copies > 0][:6]
            return render_template('member_dashboard.html',
                user=user, member=None,
                current_issues=[], due_soon=[], overdue=[],
                history=[], reservations=[],
                outstanding_fines=0, popular_books=popular_books)

        current_issues = Issue.get_by_member(member.id, status='issued')
        due_soon = [i for i in current_issues if 0 <= i.days_remaining <= 3]
        overdue = [i for i in current_issues if i.is_overdue]

        history = Issue.get_by_member(member.id, status='returned')
        history.sort(key=lambda i: i.return_date or date.min, reverse=True)
        history = history[:10]

        reservations = Reservation.get_by_member(member.id, statuses=['pending', 'available'])
        outstanding_fines = Fine.total_amount_for_member(member.id) if hasattr(Fine, 'total_amount_for_member') else sum(
            f.amount for f in Fine.get_by_member(member.id, status='pending')
        )
        popular_books = [b for b in Book.get_all() if b.available_copies > 0][:6]
    except Exception:
        member = None
        current_issues = due_soon = overdue = history = reservations = []
        outstanding_fines = 0
        popular_books = []

    return render_template('member_dashboard.html',
        user=user,
        member=member,
        current_issues=current_issues,
        due_soon=due_soon,
        overdue=overdue,
        history=history,
        reservations=reservations,
        outstanding_fines=outstanding_fines,
        popular_books=popular_books,
    )
@dashboard_bp.route('/notifications/read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Not logged in'}, 401
    from models.notification import Notification
    db_notifs = Notification.get_by_user(session['user_id'], unread_only=True)
    for n in db_notifs:
        n.update(is_read=True)
    return {'status': 'success'}
