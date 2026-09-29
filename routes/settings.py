"""
Settings routes — fully migrated to Firestore.
"""
from flask import Blueprint, render_template, request, flash, session
from models.setting import Setting
from models.user import User
from routes.auth import admin_required

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/', methods=['GET', 'POST'])
@admin_required
def index():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'library':
            Setting.set('library_name', request.form.get('library_name', ''))
            Setting.set('library_address', request.form.get('library_address', ''))
            Setting.set('library_email', request.form.get('library_email', ''))
            Setting.set('library_phone', request.form.get('library_phone', ''))
            Setting.set('fine_per_day', request.form.get('fine_per_day', '5'))
            Setting.set('max_books_per_member', request.form.get('max_books_per_member', '5'))
            Setting.set('default_borrow_days', request.form.get('default_borrow_days', '14'))
            flash('Library settings updated successfully!', 'success')

        elif action == 'profile':
            user = User.get_by_id(str(session['user_id']))
            if user:
                new_name = request.form.get('name', user.name)
                new_email = request.form.get('email', user.email)
                new_password = request.form.get('new_password', '')

                if new_password:
                    confirm_password = request.form.get('confirm_password', '')
                    if new_password != confirm_password:
                        flash('Passwords do not match.', 'danger')
                        return render_template('settings/index.html', settings=_get_settings())
                    user.set_password(new_password)

                user.update(name=new_name, email=new_email,
                            password_hash=user.password_hash)
                session['user_name'] = new_name
                flash('Profile updated successfully!', 'success')

    return render_template('settings/index.html', settings=_get_settings())


def _get_settings():
    return {
        'library_name': Setting.get('library_name', 'LPU Library Management'),
        'library_address': Setting.get('library_address', '123 University Road'),
        'library_email': Setting.get('library_email', 'library@university.edu'),
        'library_phone': Setting.get('library_phone', '+91-9876543210'),
        'fine_per_day': Setting.get('fine_per_day', '5'),
        'max_books_per_member': Setting.get('max_books_per_member', '5'),
        'default_borrow_days': Setting.get('default_borrow_days', '14'),
    }
