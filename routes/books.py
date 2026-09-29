from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from models import db
from models.book import Book
from models.issue import Issue
from routes.auth import login_required, admin_required
from sqlalchemy import or_

books_bp = Blueprint('books', __name__, url_prefix='/books')

CATEGORIES = [
    'Programming', 'Computer Science', 'Database', 'Networking',
    'Operating Systems', 'Web Development', 'Artificial Intelligence',
    'Mathematics', 'Engineering', 'Management', 'Fiction', 'Biography',
    'Science', 'History', 'Economics', 'Psychology', 'Literature', 'Other'
]

LANGUAGES = ['English', 'Hindi', 'French', 'German', 'Spanish', 'Other']

@books_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    availability = request.args.get('availability', '')
    language = request.args.get('language', '')
    sort = request.args.get('sort', 'title_asc')
    
    query = Book.query
    
    if search:
        query = query.filter(
            or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%'),
                Book.isbn.ilike(f'%{search}%')
            )
        )
    
    if category:
        query = query.filter_by(category=category)
    
    if availability == 'available':
        query = query.filter(Book.available_copies > 0)
    elif availability == 'unavailable':
        query = query.filter(Book.available_copies == 0)
    
    if language:
        query = query.filter_by(language=language)
    
    # Sorting
    if sort == 'title_asc':
        query = query.order_by(Book.title.asc())
    elif sort == 'title_desc':
        query = query.order_by(Book.title.desc())
    elif sort == 'newest':
        query = query.order_by(Book.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Book.created_at.asc())
    elif sort == 'available_first':
        query = query.order_by(Book.available_copies.desc())
    
    books = query.paginate(page=page, per_page=15, error_out=False)
    
    return render_template('books/index.html',
        books=books,
        search=search,
        category=category,
        availability=availability,
        language=language,
        sort=sort,
        categories=CATEGORIES,
        languages=LANGUAGES
    )

@books_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        isbn = request.form.get('isbn', '').strip()
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        publisher = request.form.get('publisher', '').strip()
        publication_year = request.form.get('publication_year', type=int)
        language = request.form.get('language', 'English')
        total_copies = request.form.get('total_copies', 1, type=int)
        shelf_location = request.form.get('shelf_location', '').strip()
        description = request.form.get('description', '').strip()
        cover_image = request.form.get('cover_image', '').strip()
        
        errors = []
        if not isbn: errors.append('ISBN is required.')
        if not title: errors.append('Title is required.')
        if not author: errors.append('Author is required.')
        if not category: errors.append('Category is required.')
        if total_copies < 1: errors.append('Total copies must be at least 1.')
        
        if Book.query.filter_by(isbn=isbn).first():
            errors.append(f'A book with ISBN {isbn} already exists.')
        
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('books/add.html', categories=CATEGORIES, languages=LANGUAGES, form_data=request.form)
        
        book = Book(
            isbn=isbn, title=title, author=author, category=category,
            publisher=publisher, publication_year=publication_year,
            language=language, total_copies=total_copies,
            available_copies=total_copies, shelf_location=shelf_location,
            description=description, cover_image=cover_image
        )
        db.session.add(book)
        db.session.commit()
        flash(f'Book "{title}" added successfully!', 'success')
        return redirect(url_for('books.view', id=book.id))
    
    return render_template('books/add.html', categories=CATEGORIES, languages=LANGUAGES, form_data={})

@books_bp.route('/<int:id>')
@login_required
def view(id):
    book = Book.query.get_or_404(id)
    active_issues = Issue.query.filter_by(book_id=id, status='issued').all()
    return render_template('books/view.html', book=book, active_issues=active_issues)

@books_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(id):
    book = Book.query.get_or_404(id)
    
    if request.method == 'POST':
        isbn = request.form.get('isbn', '').strip()
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        publisher = request.form.get('publisher', '').strip()
        publication_year = request.form.get('publication_year', type=int)
        language = request.form.get('language', 'English')
        total_copies = request.form.get('total_copies', 1, type=int)
        shelf_location = request.form.get('shelf_location', '').strip()
        description = request.form.get('description', '').strip()
        cover_image = request.form.get('cover_image', '').strip()
        
        errors = []
        if not isbn: errors.append('ISBN is required.')
        if not title: errors.append('Title is required.')
        if not author: errors.append('Author is required.')
        if not category: errors.append('Category is required.')
        if total_copies < 1: errors.append('Total copies must be at least 1.')
        
        existing = Book.query.filter_by(isbn=isbn).first()
        if existing and existing.id != id:
            errors.append(f'Another book with ISBN {isbn} already exists.')
        
        issued_count = book.total_copies - book.available_copies
        if total_copies < issued_count:
            errors.append(f'Cannot reduce copies below currently issued count ({issued_count}).')
        
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('books/edit.html', book=book, categories=CATEGORIES, languages=LANGUAGES)
        
        diff = total_copies - book.total_copies
        book.isbn = isbn
        book.title = title
        book.author = author
        book.category = category
        book.publisher = publisher
        book.publication_year = publication_year
        book.language = language
        book.total_copies = total_copies
        book.available_copies = book.available_copies + diff
        book.shelf_location = shelf_location
        book.description = description
        book.cover_image = cover_image
        
        db.session.commit()
        flash(f'Book "{title}" updated successfully!', 'success')
        return redirect(url_for('books.view', id=book.id))
    
    return render_template('books/edit.html', book=book, categories=CATEGORIES, languages=LANGUAGES)

@books_bp.route('/<int:id>/delete', methods=['POST'])
@admin_required
def delete(id):
    book = Book.query.get_or_404(id)
    
    active_issues = Issue.query.filter_by(book_id=id, status='issued').count()
    if active_issues > 0:
        flash(f'Cannot delete "{book.title}" — it has {active_issues} active issue(s).', 'danger')
        return redirect(url_for('books.view', id=id))
    
    title = book.title
    db.session.delete(book)
    db.session.commit()
    flash(f'Book "{title}" deleted successfully.', 'success')
    return redirect(url_for('books.index'))

@books_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    
    books = Book.query.filter(
        or_(
            Book.title.ilike(f'%{q}%'),
            Book.author.ilike(f'%{q}%'),
            Book.isbn.ilike(f'%{q}%')
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': b.id,
        'title': b.title,
        'author': b.author,
        'isbn': b.isbn,
        'available': b.available_copies > 0,
        'available_copies': b.available_copies
    } for b in books])
