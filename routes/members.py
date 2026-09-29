from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from models import db
from models.member import Member
from models.user import User
from models.issue import Issue, Reservation
from models.fine import Fine
from routes.auth import login_required, admin_required
from sqlalchemy import func
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
    
    query = Member.query
    
    if search:
        query = query.filter(
            (Member.name.ilike(f'%{search}%')) |
            (Member.email.ilike(f'%{search}%')) |
            (Member.member_id.ilike(f'%{search}%')) |
            (Member.phone.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter_by(status=status)
    
    if department:
        query = query.filter_by(department=department)
    
    members = query.order_by(Member.registration_date.desc()).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('members/index.html',
        members=members,
        search=search,
        status=status,
        department=department,
        departments=DEPARTMENTS
    )

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
        
        if Member.query.filter_by(email=email).first():
            errors.append('A member with this email already exists.')
        
        if create_account and not password:
            errors.append('Password is required when creating a login account.')
        
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('members/add.html', departments=DEPARTMENTS, form_data=request.form)
        
        member_id = generate_member_id()
        while Member.query.filter_by(member_id=member_id).first():
            member_id = generate_member_id()
        
        user_id = None
        if create_account:
            if User.query.filter_by(email=email).first():
                flash('A login account with this email already exists.', 'warning')
            else:
                from flask import current_app
                import requests
                api_key = current_app.config.get('FIREBASE_API_KEY')
                
                firebase_success = True
                if api_key and api_key != 'your_firebase_api_key_here':
                    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
                    payload = {"email": email, "password": password, "returnSecureToken": True}
                    try:
                        r = requests.post(url, json=payload, timeout=10)
                        if r.status_code != 200:
                            firebase_success = False
                            error_msg = r.json().get('error', {}).get('message', 'Firebase Error')
                            flash(f'Firebase Error: {error_msg}', 'danger')
                    except Exception as e:
                        firebase_success = False
                        flash('Failed to connect to Firebase Auth.', 'danger')
                
                if firebase_success:
                    user = User(name=name, email=email, role='member')
                    user.set_password(password)
                    db.session.add(user)
                    db.session.flush()
                    user_id = user.id
        
        member = Member(
            member_id=member_id, user_id=user_id, name=name, email=email,
            phone=phone, department=department, course=course,
            semester=semester, address=address
        )
        db.session.add(member)
        db.session.commit()
        flash(f'Member "{name}" added successfully! Member ID: {member_id}', 'success')
        return redirect(url_for('members.view', id=member.id))
    
    return render_template('members/add.html', departments=DEPARTMENTS, form_data={})

@members_bp.route('/<int:id>')
@login_required
def view(id):
    if session.get('user_role') != 'admin':
        member = Member.query.filter_by(email=session.get('user_email')).first()
        if not member or member.id != id:
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard.index'))
    
    member = Member.query.get_or_404(id)
    current_issues = Issue.query.filter_by(member_id=id, status='issued').all()
    history = Issue.query.filter_by(member_id=id, status='returned').order_by(Issue.return_date.desc()).all()
    fines = Fine.query.filter_by(member_id=id).order_by(Fine.created_at.desc()).all()
    reservations = Reservation.query.filter_by(member_id=id).order_by(Reservation.reservation_date.desc()).all()
    
    total_borrowed = Issue.query.filter_by(member_id=id).count()
    total_returned = Issue.query.filter_by(member_id=id, status='returned').count()
    total_fine = db.session.query(func.sum(Fine.amount)).filter_by(member_id=id).scalar() or 0
    
    return render_template('members/view.html',
        member=member,
        current_issues=current_issues,
        history=history,
        fines=fines,
        reservations=reservations,
        total_borrowed=total_borrowed,
        total_returned=total_returned,
        total_fine=total_fine
    )

@members_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(id):
    member = Member.query.get_or_404(id)
    
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
        
        existing = Member.query.filter_by(email=email).first()
        if existing and existing.id != id:
            errors.append('Another member with this email already exists.')
        
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('members/edit.html', member=member, departments=DEPARTMENTS)
        
        member.name = name
        member.email = email
        member.phone = phone
        member.department = department
        member.course = course
        member.semester = semester
        member.address = address
        member.status = status
        
        db.session.commit()
        flash(f'Member "{name}" updated successfully!', 'success')
        return redirect(url_for('members.view', id=member.id))
    
    return render_template('members/edit.html', member=member, departments=DEPARTMENTS)

@members_bp.route('/<int:id>/toggle-status', methods=['POST'])
@admin_required
def toggle_status(id):
    member = Member.query.get_or_404(id)
    if member.status == 'active':
        member.status = 'inactive'
        msg = f'Member "{member.name}" has been disabled.'
    else:
        member.status = 'active'
        msg = f'Member "{member.name}" has been enabled.'
    db.session.commit()
    flash(msg, 'info')
    return redirect(url_for('members.view', id=id))

@members_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    
    members = Member.query.filter(
        (Member.name.ilike(f'%{q}%')) |
        (Member.email.ilike(f'%{q}%')) |
        (Member.member_id.ilike(f'%{q}%'))
    ).filter_by(status='active').limit(10).all()
    
    return jsonify([{
        'id': m.id,
        'member_id': m.member_id,
        'name': m.name,
        'email': m.email,
        'active_issues': m.active_issues_count
    } for m in members])
