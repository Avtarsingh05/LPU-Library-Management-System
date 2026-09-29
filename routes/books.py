"""
Books routes — fully migrated to Firestore.
Uses simple Pagination helper class (no SQLAlchemy paginate()).
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from models.book import Book
from models.issue import Issue
from routes.auth import login_required, admin_required

books_bp = Blueprint('books', __name__, url_prefix='/books')

CATEGORIES = [
    'Programming', 'Computer Science', 'Database', 'Networking',
    'Operating Systems', 'Web Development', 'Artificial Intelligence',
    'Mathematics', 'Engineering', 'Management', 'Fiction', 'Biography',
    'Science', 'History', 'Economics', 'Psychology', 'Literature', 'Other'
]

LANGUAGES = ['English', 'Hindi', 'French', 'German', 'Spanish', 'Other']


class Pagination:
    """Minimal pagination helper to replace SQLAlchemy's paginate()."""
    def __init__(self, items, page, per_page):
        self.page = page
        self.per_page = per_page
        self.total = len(items)
        self.pages = max(1, (self.total + per_page - 1) // per_page)
        start = (page - 1) * per_page
        self.items = items[start: start + per_page]
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1

    def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                    (self.page - left_current - 1 < num < self.page + right_current) or
                    num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num


@books_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    availability = request.args.get('availability', '')
    language = request.args.get('language', '')
    sort = request.args.get('sort', 'title_asc')

    all_books = Book.search(search, category=category, availability=availability,
                            language=language, sort=sort)
    books = Pagination(all_books, page, per_page=15)

    return render_template('books/index.html',
        books=books, search=search, category=category,
        availability=availability, language=language, sort=sort,
        categories=CATEGORIES, languages=LANGUAGES)


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
        if Book.get_by_isbn(isbn):
            errors.append(f'A book with ISBN {isbn} already exists.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('books/add.html', categories=CATEGORIES,
                                   languages=LANGUAGES, form_data=request.form)

        book = Book(
            isbn=isbn, title=title, author=author, category=category,
            publisher=publisher, publication_year=publication_year,
            language=language, total_copies=total_copies,
            available_copies=total_copies, shelf_location=shelf_location,
            description=description, cover_image=cover_image
        )
        book.save()
        flash(f'Book "{title}" added successfully!', 'success')
        return redirect(url_for('books.view', id=book.id))

    return render_template('books/add.html', categories=CATEGORIES,
                           languages=LANGUAGES, form_data={})


@books_bp.route('/<id>')
@login_required
def view(id):
    book = Book.get_by_id(id)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books.index'))
    active_issues = Issue.get_by_book(id, status='issued')
    return render_template('books/view.html', book=book, active_issues=active_issues)


@books_bp.route('/<id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(id):
    book = Book.get_by_id(id)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books.index'))

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

        existing = Book.get_by_isbn(isbn)
        if existing and existing.id != id:
            errors.append(f'Another book with ISBN {isbn} already exists.')

        issued_count = book.total_copies - book.available_copies
        if total_copies < issued_count:
            errors.append(f'Cannot reduce copies below currently issued count ({issued_count}).')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('books/edit.html', book=book,
                                   categories=CATEGORIES, languages=LANGUAGES)

        diff = total_copies - book.total_copies
        book.update(
            isbn=isbn, title=title, author=author, category=category,
            publisher=publisher, publication_year=publication_year,
            language=language, total_copies=total_copies,
            available_copies=book.available_copies + diff,
            shelf_location=shelf_location, description=description,
            cover_image=cover_image
        )
        flash(f'Book "{title}" updated successfully!', 'success')
        return redirect(url_for('books.view', id=book.id))

    return render_template('books/edit.html', book=book,
                           categories=CATEGORIES, languages=LANGUAGES)


@books_bp.route('/<id>/delete', methods=['POST'])
@admin_required
def delete(id):
    book = Book.get_by_id(id)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books.index'))

    active_issues = Issue.get_by_book(id, status='issued')
    if active_issues:
        flash(f'Cannot delete "{book.title}" — it has {len(active_issues)} active issue(s).', 'danger')
        return redirect(url_for('books.view', id=id))

    title = book.title
    book.delete()
    flash(f'Book "{title}" deleted successfully.', 'success')
    return redirect(url_for('books.index'))


@books_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    results = Book.search(q)[:10]
    return jsonify([{
        'id': b.id,
        'title': b.title,
        'author': b.author,
        'isbn': b.isbn,
        'available': b.available_copies > 0,
        'available_copies': b.available_copies
    } for b in results])
