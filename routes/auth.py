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
import os

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
                if member:
                    if not member.department:
                        flash('Please complete your profile details to continue.', 'info')
                        return redirect(url_for('auth.onboarding'))
                    elif member.verification_status == 'rejected':
                        flash(f'Your ID card was rejected by the admin. Reason: {member.rejection_reason}. Please upload a valid ID.', 'danger')
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
        if session.get('user_role') not in ['admin', 'super_admin', 'librarian']:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return User.get_by_id(str(session['user_id']))
    return None


from extensions import limiter

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
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
                        google_photo = user_data.get('photoUrl', '')
                        if not google_photo:
                            import hashlib
                            email_hash = hashlib.md5(google_email.lower().encode('utf-8')).hexdigest()
                            google_photo = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"

                        user = User.get_by_email(google_email)
                        if not user:
                            import os
                            user = User(name=google_name, email=google_email, role='member', profile_pic=google_photo)
                            user.set_password('google_' + os.urandom(8).hex())
                            user.save()

                            # Create member profile
                            member = Member(
                                member_id="PENDING",
                                user_id=user.id,
                                name=google_name,
                                email=google_email,
                                verification_status="pending"
                            )
                            member.save()
                        elif not user.profile_pic:
                            user.update(profile_pic=google_photo)

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
                        import hashlib
                        email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
                        gravatar = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"
                        
                        user = User(name=email.split('@')[0], email=email, role='member', profile_pic=gravatar)
                        user.set_password(password)
                        user.save()
                    elif not user.profile_pic:
                        import hashlib
                        email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
                        gravatar = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"
                        user.update(profile_pic=gravatar)
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

@auth_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('signup.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('signup.html')
            
        existing_user = User.get_by_email(email)
        if existing_user:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.login'))
            
        from flask import current_app
        import requests as req
        api_key = current_app.config.get('FIREBASE_API_KEY')
        
        # Optionally create in Firebase Auth via REST API if configured
        if api_key and api_key != 'your_firebase_api_key_here':
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
            try:
                r = req.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=10)
                if r.status_code != 200:
                    error_msg = r.json().get('error', {}).get('message', 'Firebase Error')
                    flash(f'Sign up failed: {error_msg.replace("_", " ").title()}', 'danger')
                    return render_template('signup.html')
            except Exception:
                # Silently fail Firebase API integration and fallback to local DB if network issue
                pass
                
        import hashlib
        email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
        gravatar = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"
        
        user = User(name=name, email=email, role='member', profile_pic=gravatar)
        user.set_password(password)
        user.save()
        
        # Auto-login after signup
        session.permanent = True
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_role'] = user.role
        session['user_email'] = user.email
        
        # Create initial Member record
        member = Member(
            member_id="PENDING",
            user_id=user.id,
            name=user.name,
            email=user.email,
            verification_status="pending"
        )
        member.save()
        
        flash('Account created successfully! Please complete your profile setup.', 'success')
        return redirect(url_for('auth.onboarding'))
        
    return render_template('signup.html')


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

    if member.department and member.verification_status != 'rejected':
        # If they already completed onboarding profile fields, just go to dashboard
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

        id_card_file = request.files.get('id_card')
        id_card_url = member.id_card_url
        if id_card_file and id_card_file.filename:
            id_card_file.seek(0, os.SEEK_END)
            size = id_card_file.tell()
            id_card_file.seek(0)
            if size > 500 * 1024:
                errors.append("ID Card image size exceeds 500KB limit.")
            else:
                import cloudinary.uploader
                try:
                    upload_result = cloudinary.uploader.upload(id_card_file)
                    id_card_url = upload_result.get('secure_url')
                except Exception as e:
                    errors.append(f"Image upload failed: {str(e)}")
        elif not id_card_url:
            errors.append('ID Card image is required for verification.')

        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            member.update(
                phone=phone,
                department=department,
                course=course,
                semester=semester,
                address=address,
                id_card_url=id_card_url,
                verification_status='pending'
            )
            flash('Profile updated! Your account is pending admin verification, but you can now explore the library.', 'success')
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
            admin = User(name='System Admin', email='avtar10@admin.com', role='super_admin')
            admin.set_password('Avtar@10')
            admin.save()
            results['status'] = 'Created avtar10@admin.com in Firestore!'
            results['id'] = admin.id
        else:
            existing.set_password('Avtar@10')
            existing.role = 'super_admin'
            existing.save()
            results['status'] = 'Updated avtar10@admin.com password and role in Firestore!'
            results['id'] = existing.id
        results['db'] = 'Firestore'
    except Exception as e:
        results['error'] = str(e)
        results['type'] = str(type(e))
    return jsonify(results)

@auth_bp.route('/reupload_id', methods=['POST'])
@login_required
def reupload_id():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    member_profiles = user.member_profile
    if not member_profiles:
        return redirect(url_for('dashboard.index'))
        
    member = member_profiles[0]
    if member.verification_status != 'rejected':
        flash("Your ID is not in a rejected state.", "info")
        return redirect(url_for('dashboard.index'))
        
    file = request.files.get('id_card')
    if not file or not file.filename:
        flash("Please provide an image.", "danger")
        return redirect(url_for('dashboard.index'))
        
    # Check size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 500 * 1024:
        flash("Image size exceeds 500KB limit.", "danger")
        return redirect(url_for('dashboard.index'))
        
    try:
        import cloudinary.uploader
        result = cloudinary.uploader.upload(file)
        
        member.update(
            id_card_url=result.get('secure_url'),
            verification_status='pending',
            rejection_reason=''
        )
        flash("ID card re-uploaded successfully. Awaiting admin approval.", "success")
    except Exception as e:
        flash(f"Error uploading image: {str(e)}", "danger")
        
    return redirect(url_for('dashboard.index'))
