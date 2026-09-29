from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models.user import User
from models.library import Library
from models.librarian_assignment import LibrarianAssignment
from models import get_db

libraries_bp = Blueprint('libraries', __name__, url_prefix='/libraries')

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        user = User.get_by_id(str(session['user_id']))
        if not user or not user.is_super_admin():
            flash('Access denied. Super Admin only.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@libraries_bp.route('/')
@super_admin_required
def index():
    libraries = Library.get_all()
    return render_template('libraries/index.html', libraries=libraries)

@libraries_bp.route('/add', methods=['GET', 'POST'])
@super_admin_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        address = request.form.get('address')
        
        lib = Library(name=name, code=code, description=description, address=address)
        lib.save()
        flash('Library added successfully.', 'success')
        return redirect(url_for('libraries.index'))
    return render_template('libraries/add.html')

@libraries_bp.route('/edit/<lib_id>', methods=['GET', 'POST'])
@super_admin_required
def edit(lib_id):
    lib = Library.get_by_id(lib_id)
    if not lib:
        flash('Library not found.', 'danger')
        return redirect(url_for('libraries.index'))
        
    if request.method == 'POST':
        lib.update(
            name=request.form.get('name'),
            code=request.form.get('code'),
            description=request.form.get('description'),
            address=request.form.get('address'),
            status=request.form.get('status', 'active')
        )
        flash('Library updated successfully.', 'success')
        return redirect(url_for('libraries.index'))
    return render_template('libraries/edit.html', library=lib)

@libraries_bp.route('/<lib_id>/librarians', methods=['GET', 'POST'])
@super_admin_required
def manage_librarians(lib_id):
    lib = Library.get_by_id(lib_id)
    if not lib:
        flash('Library not found.', 'danger')
        return redirect(url_for('libraries.index'))

    assignments = LibrarianAssignment.get_by_library(lib_id)
    assigned_ids = [a.librarian_id for a in assignments]
    
    # Get all librarians to allow assignment
    all_users = get_db().collection('users').where('role', '==', 'librarian').stream()
    librarians = [User._from_doc(d) for d in all_users]
    
    assigned_librarians = [l for l in librarians if l.id in assigned_ids]
    available_librarians = [l for l in librarians if l.id not in assigned_ids]

    if request.method == 'POST':
        librarian_id = request.form.get('librarian_id')
        if librarian_id:
            LibrarianAssignment(librarian_id=librarian_id, library_id=lib_id).save()
            flash('Librarian assigned successfully.', 'success')
        return redirect(url_for('libraries.manage_librarians', lib_id=lib_id))
        
    return render_template('libraries/librarians.html', library=lib, 
                           assigned_librarians=assigned_librarians,
                           available_librarians=available_librarians)

@libraries_bp.route('/<lib_id>/librarians/<librarian_id>/remove', methods=['POST'])
@super_admin_required
def remove_librarian(lib_id, librarian_id):
    LibrarianAssignment.remove_assignment(librarian_id, lib_id)
    flash('Librarian removed from library.', 'success')
    return redirect(url_for('libraries.manage_librarians', lib_id=lib_id))

from routes.auth import login_required
from flask import jsonify

@libraries_bp.route('/<lib_id>/books/<book_id>/copies', methods=['GET'])
@login_required
def get_available_copies(lib_id, book_id):
    from models.book_copy import BookCopy
    all_copies = BookCopy.get_by_book(book_id)
    available_in_lib = [c for c in all_copies if c.library_id == lib_id and c.status == 'AVAILABLE']
    
    return jsonify([{
        'id': c.id,
        'condition': c.condition
    } for c in available_in_lib])
