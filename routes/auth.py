from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models import db
from models.user import User
from models.member import Member
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Check onboarding for members
        if request.endpoint != 'auth.onboarding' and session.get('user_role') == 'member':
            user_id = session.get('user_id')
            member = Member.query.filter_by(user_id=user_id).first()
            if member and not member.department:
                flash('Please complete your profile details to continue.', 'info')
                return redirect(url_for('auth.onboarding'))
                
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember_me') == 'on'
        id_token = request.form.get('firebase_id_token')
        
        from flask import current_app
        import requests
        api_key = current_app.config.get('FIREBASE_API_KEY')
        
        # --- Handle Google Sign-in via id_token ---
        if id_token and api_key and api_key != 'your_firebase_api_key_here':
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
            try:
                r = requests.post(url, json={"idToken": id_token}, timeout=10)
                if r.status_code == 200:
                    user_data = r.json().get('users', [{}])[0]
                    google_email = user_data.get('email')
                    google_name = user_data.get('displayName', 'Google User')
                    
                    user = User.query.filter_by(email=google_email).first()
                    if not user:
                        # Auto-create member if they login via Google
                        import os as built_in_os
                        user = User(name=google_name, email=google_email, role='member')
                        user.set_password('generated_' + built_in_os.urandom(8).hex())
                        db.session.add(user)
                        db.session.flush()
                        
                        
                        from models.member import Member
                        import random
                        import string
                        year = __import__('datetime').date.today().year
                        suffix = ''.join(random.choices(string.digits, k=4))
                        member_id = f'LIB{year}{suffix}'
                        while Member.query.filter_by(member_id=member_id).first():
                            suffix = ''.join(random.choices(string.digits, k=4))
                            member_id = f'LIB{year}{suffix}'
                        member = Member(member_id=member_id, user_id=user.id, name=google_name, email=google_email)
                        db.session.add(member)
                        db.session.commit()
                        
                    session.permanent = True
                    session['user_id'] = user.id
                    session['user_name'] = user.name
                    session['user_role'] = user.role
                    session['user_email'] = user.email
                    
                    flash(f'Welcome back, {user.name}!', 'success')
                    return redirect(url_for('dashboard.index'))
                else:
                    flash('Google Authentication failed.', 'danger')
                    return render_template('login.html')
            except Exception:
                flash('Authentication service unavailable.', 'danger')
                return render_template('login.html')

        # --- Handle standard Email/Password Sign-in ---
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        # Check if Firebase is configured
        from flask import current_app
        import requests
        api_key = current_app.config.get('FIREBASE_API_KEY')
        
        is_authenticated = False
        
        if api_key and api_key != 'your_firebase_api_key_here':
            # Use Firebase REST API to authenticate
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
            payload = {"email": email, "password": password, "returnSecureToken": True}
            try:
                r = requests.post(url, json=payload, timeout=10)
                if r.status_code == 200:
                    is_authenticated = True
            except requests.exceptions.RequestException:
                flash('Authentication service is currently unavailable.', 'danger')
                return render_template('login.html')
        else:
            # Fallback to local DB check if Firebase is not configured
            if user and user.check_password(password):
                is_authenticated = True

        if is_authenticated and user:
            if not user.is_active:
                flash('Your account has been disabled. Please contact the librarian.', 'danger')
                return render_template('login.html')
            
            session.permanent = remember
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            session['user_email'] = user.email
            
            flash(f'Welcome back, {user.name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'You have been logged out successfully. Goodbye, {user_name}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    if session.get('user_role') != 'member':
        return redirect(url_for('dashboard.index'))
        
    user_id = session['user_id']
    member = Member.query.filter_by(user_id=user_id).first()
    
    if not member:
        return redirect(url_for('auth.login'))
        
    if member.department and request.method == 'GET':
        # Already onboarded
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        course = request.form.get('course', '').strip()
        semester = request.form.get('semester', '').strip()
        address = request.form.get('address', '').strip()
        
        errors = []
        if not phone: errors.append('Phone number is required.')
        if not department: errors.append('Department is required.')
        if not course: errors.append('Course is required.')
        
        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            member.phone = phone
            member.department = department
            member.course = course
            member.semester = semester
            member.address = address
            db.session.commit()
            flash('Profile completed successfully! Welcome to the library.', 'success')
            return redirect(url_for('dashboard.index'))
            
    # Need to pass DEPARTMENTS for the form
    DEPARTMENTS = [
        'Computer Science', 'Information Technology', 'Electronics',
        'Mechanical Engineering', 'Civil Engineering', 'Mathematics',
        'Physics', 'Chemistry', 'Management', 'Commerce', 'Arts', 'Other'
    ]
    return render_template('onboarding.html', departments=DEPARTMENTS, member=member)
