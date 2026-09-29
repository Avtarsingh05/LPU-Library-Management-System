"""
Auth routes — fully migrated to Firestore.
No SQLAlchemy. Uses User and Member Firestore models.
"""
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from models.user import User
from models.member import Member
from functools import wraps
import random
import string

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))

        # Check onboarding for members
        if request.endpoint != 'auth.onboarding' and session.get('user_role') == 'member':
            user_id = str(session.get('user_id'))
            try:
                member = Member.get_by_user_id(user_id)
                if member and not member.department:
                    flash('Please complete your profile details to continue.', 'info')
                    return redirect(url_for('auth.onboarding'))
            except Exception:
                pass

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
        return User.get_by_id(str(session['user_id']))
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
        import requests as req
        api_key = current_app.config.get('FIREBASE_API_KEY')

        # ── Google Sign-In via id_token ─────────────────────────────────────
        if id_token:
            if api_key:
                url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
                try:
                    r = req.post(url, json={"idToken": id_token}, timeout=10)
                    if r.status_code == 200:
                        user_data = r.json().get('users', [{}])[0]
                        google_email = user_data.get('email')
                        google_name = user_data.get('displayName', 'Google User')

                        user = User.get_by_email(google_email)
                        if not user:
                            import os
                            user = User(name=google_name, email=google_email, role='member')
                            user.set_password('google_' + os.urandom(8).hex())
                            user.save()

                            # Create member profile
                            year = __import__('datetime').date.today().year
                            suffix = ''.join(random.choices(string.digits, k=4))
                            member_id_str = f'LIB{year}{suffix}'
                            while Member.get_by_member_id(member_id_str):
                                suffix = ''.join(random.choices(string.digits, k=4))
                                member_id_str = f'LIB{year}{suffix}'
                            member = Member(
                                member_id=member_id_str,
                                user_id=user.id,
                                name=google_name,
                                email=google_email
                            )
                            member.save()

                        session.permanent = True
                        session['user_id'] = user.id
                        session['user_name'] = user.name
                        session['user_role'] = user.role
                        session['user_email'] = user.email
                        flash(f'Welcome back, {user.name}!', 'success')
                        return redirect(url_for('dashboard.index'))
                    else:
                        flash('Google account verification failed. Please try again.', 'danger')
                        return render_template('login.html')
                except req.exceptions.RequestException:
                    flash('Google Authentication network timeout. Please retry.', 'danger')
                    return render_template('login.html')
                except Exception as ex:
                    flash(f'Authentication error: {ex}', 'danger')
                    return render_template('login.html')

        # ── Email/Password Sign-In ──────────────────────────────────────────
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')

        user = None
        is_authenticated = False

        try:
            user = User.get_by_email(email)
        except Exception:
            user = None

        # 1. Check Firestore password
        if user and user.check_password(password):
            is_authenticated = True

        # 2. Fallback: Firebase REST Auth (for users registered via Firebase Console)
        if not is_authenticated and api_key:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
            payload = {"email": email, "password": password, "returnSecureToken": True}
            try:
                r = req.post(url, json=payload, timeout=10)
                if r.status_code == 200:
                    is_authenticated = True
                    if not user:
                        user = User(name=email.split('@')[0], email=email, role='member')
                        user.set_password(password)
                        user.save()
            except Exception:
                pass

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

    user_id = str(session['user_id'])
    member = Member.get_by_user_id(user_id)
    if not member:
        return redirect(url_for('auth.login'))

    if member.department and request.method == 'GET':
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
            member.update(
                phone=phone,
                department=department,
                course=course,
                semester=semester,
                address=address
            )
            flash('Profile completed successfully! Welcome to the library.', 'success')
            return redirect(url_for('dashboard.index'))

    DEPARTMENTS = [
        'Computer Science', 'Information Technology', 'Electronics',
        'Mechanical Engineering', 'Civil Engineering', 'Mathematics',
        'Physics', 'Chemistry', 'Management', 'Commerce', 'Arts', 'Other'
    ]
    return render_template('onboarding.html', departments=DEPARTMENTS, member=member)


@auth_bp.route('/init-admin')
def init_admin():
    """Diagnostic endpoint to seed the admin user in Firestore."""
    results = {}
    try:
        existing = User.get_by_email('avtar10@admin.com')
        if not existing:
            admin = User(name='System Admin', email='avtar10@admin.com', role='admin')
            admin.set_password('Avtar@10')
            admin.save()
            results['status'] = 'Created avtar10@admin.com in Firestore!'
            results['id'] = admin.id
        else:
            existing.set_password('Avtar@10')
            existing.save()
            results['status'] = 'Updated avtar10@admin.com password in Firestore!'
            results['id'] = existing.id
        results['db'] = 'Firestore'
    except Exception as e:
        results['error'] = str(e)
        results['type'] = str(type(e))
    return jsonify(results)
