"""
Members routes — fully migrated to Firestore.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from models.member import Member
from models.user import User
from models.issue import Issue, Reservation
from models.fine import Fine
from routes.auth import login_required, admin_required
from routes.books import Pagination
import random
import string

members_bp = Blueprint('members', __name__, url_prefix='/members')

DEPARTMENTS = [
    'Computer Science', 'Information Technology', 'Electronics',
    'Mechanical Engineering', 'Civil Engineering', 'Mathematics',
    'Physics', 'Chemistry', 'Management', 'Commerce', 'Arts', 'Other'
]


def generate_member_id():
    year = __import__('datetime').date.today().year
    suffix = ''.join(random.choices(string.digits, k=4))
    return f'LIB{year}{suffix}'


@members_bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')
    department = request.args.get('department', '')

    all_members = Member.search(query_text=search, status=status, department=department)
    members = Pagination(all_members, page, per_page=15)

    return render_template('members/index.html',
        members=members, search=search, status=status,
        department=department, departments=DEPARTMENTS)


@members_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        course = request.form.get('course', '').strip()
        semester = request.form.get('semester', '').strip()
        address = request.form.get('address', '').strip()
        create_account = request.form.get('create_account') == 'on'
        password = request.form.get('password', '').strip()

        errors = []
        if not name: errors.append('Name is required.')
        if not email: errors.append('Email is required.')
        if Member.get_by_email(email):
            errors.append('A member with this email already exists.')
        if create_account and not password:
            errors.append('Password is required when creating a login account.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('members/add.html', departments=DEPARTMENTS, form_data=request.form)

        # Generate unique member_id
        member_id_str = generate_member_id()
        while Member.get_by_member_id(member_id_str):
            member_id_str = generate_member_id()

        user_id = None
        if create_account:
            if User.get_by_email(email):
                flash('A login account with this email already exists.', 'warning')
            else:
                from flask import current_app
                import requests as req
                api_key = current_app.config.get('FIREBASE_API_KEY')
                firebase_success = True

                if api_key:
                    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
                    try:
                        r = req.post(url, json={"email": email, "password": password,
                                                "returnSecureToken": True}, timeout=10)
                        if r.status_code != 200:
                            firebase_success = False
                            error_msg = r.json().get('error', {}).get('message', 'Firebase Error')
                            flash(f'Firebase Error: {error_msg}', 'danger')
                    except Exception:
                        firebase_success = False
                        flash('Failed to connect to Firebase Auth.', 'danger')

                if firebase_success:
                    new_user = User(name=name, email=email, role='member')
                    new_user.set_password(password)
                    new_user.save()
                    user_id = new_user.id

        member = Member(
            member_id=member_id_str, user_id=user_id, name=name, email=email,
            phone=phone, department=department, course=course,
            semester=semester, address=address
        )
        member.save()
        flash(f'Member "{name}" added successfully! Member ID: {member_id_str}', 'success')
        return redirect(url_for('members.view', id=member.id))

    return render_template('members/add.html', departments=DEPARTMENTS, form_data={})


@members_bp.route('/<id>')
@login_required
def view(id):
    if session.get('user_role') != 'admin':
        my_member = Member.get_by_email(session.get('user_email', ''))
        if not my_member or my_member.id != id:
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard.index'))

    member = Member.get_by_id(id)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('members.index'))

    current_issues = Issue.get_by_member(id, status='issued')
    history = Issue.get_by_member(id, status='returned')
    history.sort(key=lambda i: i.return_date or __import__('datetime').date.min, reverse=True)

    fines = Fine.get_by_member(id)
    reservations = Reservation.get_by_member(id)

    all_issues = Issue.get_by_member(id)
    total_borrowed = len(all_issues)
    total_returned = len([i for i in all_issues if i.status == 'returned'])
    total_fine = sum(f.amount for f in fines)

    return render_template('members/view.html',
        member=member,
        current_issues=current_issues,
        history=history,
        fines=fines,
        reservations=reservations,
        total_borrowed=total_borrowed,
        total_returned=total_returned,
        total_fine=total_fine,
    )


@members_bp.route('/<id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(id):
    member = Member.get_by_id(id)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('members.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        course = request.form.get('course', '').strip()
        semester = request.form.get('semester', '').strip()
        address = request.form.get('address', '').strip()
        status = request.form.get('status', 'active')

        errors = []
        if not name: errors.append('Name is required.')
        if not email: errors.append('Email is required.')
        existing = Member.get_by_email(email)
        if existing and existing.id != id:
            errors.append('Another member with this email already exists.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('members/edit.html', member=member, departments=DEPARTMENTS)

        member.update(name=name, email=email, phone=phone, department=department,
                      course=course, semester=semester, address=address, status=status)
        flash(f'Member "{name}" updated successfully!', 'success')
        return redirect(url_for('members.view', id=member.id))

    return render_template('members/edit.html', member=member, departments=DEPARTMENTS)


@members_bp.route('/<id>/toggle-status', methods=['POST'])
@admin_required
def toggle_status(id):
    member = Member.get_by_id(id)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('members.index'))

    new_status = 'inactive' if member.status == 'active' else 'active'
    member.update(status=new_status)
    verb = 'disabled' if new_status == 'inactive' else 'enabled'
    flash(f'Member "{member.name}" has been {verb}.', 'info')
    return redirect(url_for('members.view', id=id))


@members_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    results = Member.search(query_text=q, status='active')[:10]
    return jsonify([{
        'id': m.id,
        'member_id': m.member_id,
        'name': m.name,
        'email': m.email,
        'active_issues': m.active_issues_count,
    } for m in results])
