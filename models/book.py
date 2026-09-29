"""
Book model backed by Firestore.
Collection: 'books'
Document ID: auto-generated UUID
"""
from models import get_db
from datetime import datetime
import uuid


class Book:
    COLLECTION = 'books'

    def __init__(self, id=None, isbn='', title='', author='', category='',
                 publisher='', publication_year=None, language='English',
                 total_copies=1, available_copies=1, shelf_location='',
                 description='', cover_image='', created_at=None):
        self.id = id or str(uuid.uuid4())
        self.isbn = isbn
        self.title = title
        self.author = author
        self.category = category
        self.publisher = publisher
        self.publication_year = publication_year
        self.language = language
        self.total_copies = total_copies
        self.available_copies = available_copies
        self.shelf_location = shelf_location
        self.description = description
        self.cover_image = cover_image
        self.created_at = created_at or datetime.utcnow()

    @property
    def issued_copies(self):
        return self.total_copies - self.available_copies

    @property
    def is_available(self):
        return self.available_copies > 0

    # ── Persistence ──────────────────────────────────────────────────────────
    def _to_dict(self):
        return {
            'id': self.id,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'category': self.category,
            'publisher': self.publisher,
            'publication_year': self.publication_year,
            'language': self.language,
            'total_copies': self.total_copies,
            'available_copies': self.available_copies,
            'shelf_location': self.shelf_location,
            'description': self.description,
            'cover_image': self.cover_image,
            'created_at': self.created_at,
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        return self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        return self

    def delete(self):
        get_db().collection(self.COLLECTION).document(self.id).delete()

    # ── Class-level queries ──────────────────────────────────────────────────
    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            isbn=d.get('isbn', ''),
            title=d.get('title', ''),
            author=d.get('author', ''),
            category=d.get('category', ''),
            publisher=d.get('publisher', ''),
            publication_year=d.get('publication_year'),
            language=d.get('language', 'English'),
            total_copies=d.get('total_copies', 1),
            available_copies=d.get('available_copies', 1),
            shelf_location=d.get('shelf_location', ''),
            description=d.get('description', ''),
            cover_image=d.get('cover_image', ''),
            created_at=d.get('created_at'),
        )

    @classmethod
    def get_by_id(cls, bid):
        doc = get_db().collection(cls.COLLECTION).document(bid).get()
        if doc.exists:
            return cls._from_doc(doc)
        return None

    @classmethod
    def get_by_isbn(cls, isbn):
        docs = get_db().collection(cls.COLLECTION)\
                       .where('isbn', '==', isbn).limit(1).stream()
        for doc in docs:
            return cls._from_doc(doc)
        return None

    @classmethod
    def get_all(cls):
        """Return all books, sorted by title."""
        docs = get_db().collection(cls.COLLECTION).stream()
        books = [cls._from_doc(d) for d in docs if d.to_dict()]
        books.sort(key=lambda b: (b.title or '').lower())
        return books

    @classmethod
    def search(cls, query_text, category='', availability='', language='', sort='title_asc'):
        """Client-side filtered search over all books."""
        all_books = cls.get_all()
        q = query_text.lower() if query_text else ''
        result = []
        for b in all_books:
            if q and not (q in b.title.lower() or q in b.author.lower() or q in b.isbn.lower()):
                continue
            if category and b.category != category:
                continue
            if availability == 'available' and b.available_copies <= 0:
                continue
            if availability == 'unavailable' and b.available_copies > 0:
                continue
            if language and b.language != language:
                continue
            result.append(b)

        if sort == 'title_desc':
            result.sort(key=lambda b: (b.title or '').lower(), reverse=True)
        elif sort == 'newest':
            result.sort(key=lambda b: b.created_at or datetime.min, reverse=True)
        elif sort == 'oldest':
            result.sort(key=lambda b: b.created_at or datetime.min)
        elif sort == 'available_first':
            result.sort(key=lambda b: b.available_copies, reverse=True)
        else:  # title_asc (default)
            result.sort(key=lambda b: (b.title or '').lower())
        return result

    @classmethod
    def count(cls):
        docs = get_db().collection(cls.COLLECTION).stream()
        return sum(1 for _ in docs)

    @classmethod
    def total_available(cls):
        docs = get_db().collection(cls.COLLECTION).stream()
        return sum(d.to_dict().get('available_copies', 0) for d in docs if d.to_dict())

    def __repr__(self):
        return f'<Book {self.title}>'
