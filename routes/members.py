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
import os

members_bp = Blueprint('members', __name__, url_prefix='/members')

DEPARTMENTS = [
    'Computer Science', 'Information Technology', 'Electronics',
    'Mechanical Engineering', 'Civil Engineering', 'Mathematics',
    'Physics', 'Chemistry', 'Management', 'Commerce', 'Arts', 'Other'
]


def generate_member_id(role='member'):
    """Generate a truly unique real ID: 6 digits for members, 5 digits for librarians."""
    import random
    if role in ['librarian', 'admin', 'super_admin']:
        # 5-digit ID (10000 - 99999)
        return str(random.randint(10000, 99999))
    else:
        # 6-digit ID (100000 - 999999)
        return str(random.randint(100000, 999999))


@members_bp.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    member = Member.get_by_user_id(str(user_id))
    if member:
        return redirect(url_for('members.view', id=member.id))
    # If no member profile found, maybe they are super admin or haven't onboarded
    if session.get('user_role') in ['admin', 'super_admin']:
        flash('Admins do not have a separate member profile.', 'info')
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.onboarding'))

@members_bp.route('/<id>/upload_pic', methods=['POST'])
@login_required
def upload_pic(id):
    member = Member.get_by_id(id)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    if str(session.get('user_id')) != member.user_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('members.view', id=id))

    pic = request.files.get('profile_pic')
    if pic and pic.filename:
        pic.seek(0, os.SEEK_END)
        size = pic.tell()
        pic.seek(0)
        if size > 500 * 1024:
            flash('Image size exceeds 500KB limit.', 'danger')
            return redirect(url_for('members.view', id=id))
        import cloudinary.uploader
        try:
            res = cloudinary.uploader.upload(pic)
            url = res.get('secure_url')
            if url:
                user = User.get_by_id(member.user_id)
                if user:
                    user.update(profile_pic=url)
                    flash('Profile picture updated successfully.', 'success')
        except Exception as e:
            flash(f"Image upload failed: {e}", 'danger')
            
    return redirect(url_for('members.view', id=id))

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
    if session.get('user_role') not in ['admin', 'super_admin', 'librarian']:
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
    
    member_user = None
    if member.user_id:
        member_user = User.get_by_id(member.user_id)

    return render_template('members/view.html',
        member=member,
        member_user=member_user,
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

@members_bp.route('/<id>/edit_uid', methods=['POST'])
@admin_required
def edit_uid(id):
    if session.get('user_role') != 'super_admin':
        flash('Only super admins can change a UID manually.', 'danger')
        return redirect(url_for('members.view', id=id))

    member = Member.get_by_id(id)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('members.index'))
        
    new_uid = request.form.get('new_uid', '').strip()
    if not new_uid:
        flash('New UID cannot be empty.', 'danger')
        return redirect(url_for('members.view', id=id))
        
    existing = Member.get_by_member_id(new_uid)
    if existing and existing.id != member.id:
        flash(f'UID "{new_uid}" is already in use by another member.', 'danger')
        return redirect(url_for('members.view', id=id))
        
    member.update(member_id=new_uid)
    flash(f'Successfully changed {member.name}\'s UID to {new_uid}.', 'success')
    return redirect(url_for('members.view', id=id))



@members_bp.route('/<id>/promote', methods=['POST'])
@admin_required
def promote(id):
    if session.get('user_role') not in ['admin', 'super_admin']:
        flash('Only admins can promote users.', 'danger')
        return redirect(url_for('members.view', id=id))

    member = Member.get_by_id(id)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('members.index'))
        
    if not member.user_id:
        flash('This member does not have a login account attached.', 'warning')
        return redirect(url_for('members.view', id=id))
        
    user = User.get_by_id(member.user_id)
    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('members.view', id=id))
        
    new_role = request.form.get('role')
    if new_role not in ['member', 'librarian', 'admin', 'super_admin']:
        flash('Invalid role specified.', 'danger')
        return redirect(url_for('members.view', id=id))
        
    if new_role == 'super_admin' and session.get('user_role') != 'super_admin':
        flash('Only a super admin can create another super admin.', 'danger')
        return redirect(url_for('members.view', id=id))
        
    user.role = new_role
    user.save()
    
    # Update member_id if role changes to librarian/admin (5 digits) or member (6 digits)
    import random
    new_member_id = None
    if new_role in ['librarian', 'admin', 'super_admin'] and len(member.member_id) != 5:
        new_member_id = str(random.randint(10000, 99999))
    elif new_role == 'member' and len(member.member_id) != 6:
        new_member_id = str(random.randint(100000, 999999))
        
    if new_member_id:
        while Member.get_by_member_id(new_member_id):
            new_member_id = str(random.randint(10000, 99999) if new_role != 'member' else random.randint(100000, 999999))
        member.update(member_id=new_member_id)
        flash(f'Successfully changed {member.name}\'s role to {new_role.capitalize()} and assigned new unique ID {new_member_id}.', 'success')
    else:
        flash(f'Successfully changed {member.name}\'s role to {new_role.capitalize()}.', 'success')
        
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

@members_bp.route('/<id>/verify', methods=['POST'])
@admin_required
def verify(id):
    member = Member.get_by_id(id)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('members.index'))
        
    action = request.form.get('action')
    
    if action == 'approve':
        import random
        # Only assign an ID if they don't have a valid one
        new_member_id = member.member_id
        if not new_member_id or new_member_id == 'PENDING':
            # Check user role if they have one attached to assign correct length
            is_librarian = False
            if member.user_id:
                user = User.get_by_id(member.user_id)
                if user and user.role in ['librarian', 'admin', 'super_admin']:
                    is_librarian = True
                    
            if is_librarian:
                new_member_id = str(random.randint(10000, 99999))
            else:
                new_member_id = str(random.randint(100000, 999999))
                
            while Member.get_by_member_id(new_member_id):
                new_member_id = str(random.randint(10000, 99999) if is_librarian else random.randint(100000, 999999))
                
        member.update(verification_status='approved', member_id=new_member_id, rejection_reason='')
        flash(f'{member.name} has been verified and assigned ID: {new_member_id}', 'success')
        
    elif action == 'reject':
        reason = request.form.get('rejection_reason', '').strip()
        if not reason:
            flash('You must provide a reason for rejecting the ID card.', 'danger')
            return redirect(url_for('members.view', id=id))
        member.update(verification_status='rejected', rejection_reason=reason, id_card_url='')
        flash(f'ID verification rejected for {member.name}.', 'warning')
        
    return redirect(url_for('members.view', id=id))

@members_bp.route('/<id>/notify', methods=['POST'])
@login_required
@admin_required
def notify(id):
    member = Member.get_by_id(id)
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.index'))
        
    title = request.form.get('title', '').strip()
    message = request.form.get('message', '').strip()
    type_ = request.form.get('type', 'info')
    
    if not title or not message:
        flash('Title and message are required', 'danger')
        return redirect(url_for('members.view', id=id))
        
    if member.user_id:
        from models.notification import Notification
        notif = Notification(
            user_id=member.user_id,
            title=title,
            message=message,
            type=type_
        )
        notif.save()
        flash('Notification sent successfully', 'success')
    else:
        flash('Cannot send notification: Member does not have an associated user account', 'warning')
        
    return redirect(url_for('members.view', id=id))
@members_bp.route('/notify_all', methods=['POST'])
@login_required
@admin_required
def notify_all():
    title = request.form.get('title', '').strip()
    message = request.form.get('message', '').strip()
    type_ = request.form.get('type', 'info')
    
    if not title or not message:
        flash('Title and message are required', 'danger')
        return redirect(url_for('members.index'))
        
    from models.user import User
    from models.notification import Notification
    
    users = User.get_all()
    # Batch write logic for Firestore
    from models import get_db
    db = get_db()
    batch = db.batch()
    count = 0
    
    for u in users:
        notif = Notification(user_id=u.id, title=title, message=message, type=type_)
        doc_ref = db.collection(Notification.COLLECTION).document(notif.id)
        batch.set(doc_ref, notif._to_dict())
        
        from models.notification import _notif_cache
        if u.id in _notif_cache:
            del _notif_cache[u.id]
            
        count += 1
        if count >= 490:
            batch.commit()
            batch = db.batch()
            count = 0
            
    if count > 0:
        batch.commit()
        
    flash(f'Global notification sent to {len(users)} users successfully', 'success')
    return redirect(url_for('members.index'))

@members_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user_id = session.get('user_id')
    member = Member.get_by_user_id(str(user_id))
    if not member:
        flash('Profile not found.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    department = request.form.get('department', '').strip()
    course = request.form.get('course', '').strip()
    address = request.form.get('address', '').strip()
    
    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('members.view', id=member.id))
        
    member.update(
        name=name,
        phone=phone,
        department=department,
        course=course,
        address=address
    )
    
    # Also update user document name
    from models.user import User
    user = User.get_by_id(str(user_id))
    if user and user.name != name:
        user.update(name=name)
        
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('members.view', id=member.id))

