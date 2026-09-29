from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.e_resource import EResource
from routes.auth import login_required, get_current_user
import uuid

elibrary_bp = Blueprint('elibrary', __name__, url_prefix='/elibrary')

@elibrary_bp.route('/')
@login_required
def index():
    user = get_current_user()
    resources = EResource.get_all()
    
    # Filter by access level
    allowed_resources = []
    for r in resources:
        if r.status != 'ACTIVE' and not user.is_admin():
            continue
        if r.access_level == 'PUBLIC':
            allowed_resources.append(r)
        elif r.access_level == 'MEMBERS_ONLY' and (user.role == 'member' or user.is_admin() or user.is_librarian()):
            # For members, they must be fully verified
            if user.role == 'member':
                from models.member import Member
                member = Member.get_by_email(user.email)
                if member and member.verification_status == 'approved':
                    allowed_resources.append(r)
            else:
                allowed_resources.append(r)
        elif r.access_level == 'LIBRARY_ONLY' and (user.is_admin() or user.is_librarian()):
            # In a full implementation, check if member belongs to this library
            allowed_resources.append(r)
        elif r.access_level == 'ADMIN_ONLY' and (user.is_admin() or user.is_super_admin()):
            allowed_resources.append(r)

    return render_template('elibrary/index.html', resources=allowed_resources, user=user)

@elibrary_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    user = get_current_user()
    if not user.is_admin() and not user.is_librarian():
        flash('Access denied.', 'danger')
        return redirect(url_for('elibrary.index'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        author = request.form.get('author')
        access_level = request.form.get('access_level', 'PUBLIC')
        file_url = request.form.get('file_url') # Mock upload for now
        
        EResource(
            title=title,
            description=description,
            category=category,
            author=author,
            access_level=access_level,
            file_url=file_url,
            uploaded_by=user.id
        ).save()
        
        flash('E-Resource added successfully.', 'success')
        return redirect(url_for('elibrary.index'))
        
    return render_template('elibrary/add.html')
