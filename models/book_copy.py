"""
BookCopy model representing a physical copy of a book in a library.
Collection: 'bookCopies'
"""
from models import get_db
from datetime import datetime
import uuid

class BookCopy:
    COLLECTION = 'bookCopies'

    def __init__(self, id=None, book_id='', library_id='', barcode='', qr_code='',
                 status='AVAILABLE', condition='NEW', condition_notes='',
                 building='', floor='', section='', rack='', shelf='', position='',
                 created_at=None, updated_at=None):
        self.id = id or str(uuid.uuid4())
        self.book_id = book_id
        self.library_id = library_id
        self.barcode = barcode
        self.qr_code = qr_code
        self.status = status # AVAILABLE, ISSUED, OVERDUE, RESERVED, LOST, DAMAGED, UNDER_REPAIR, MISSING
        self.condition = condition # NEW, EXCELLENT, GOOD, FAIR, DAMAGED, UNDER_REPAIR, LOST
        self.condition_notes = condition_notes
        self.building = building
        self.floor = floor
        self.section = section
        self.rack = rack
        self.shelf = shelf
        self.position = position
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def _to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'library_id': self.library_id,
            'barcode': self.barcode,
            'qr_code': self.qr_code,
            'status': self.status,
            'condition': self.condition,
            'condition_notes': self.condition_notes,
            'building': self.building,
            'floor': self.floor,
            'section': self.section,
            'rack': self.rack,
            'shelf': self.shelf,
            'position': self.position,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def save(self):
        self.updated_at = datetime.utcnow()
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        BookCopy._cache_get_all = None
        return self

    def update(self, **kwargs):
        kwargs['updated_at'] = datetime.utcnow()
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        BookCopy._cache_get_all = None
        return self

    def delete(self):
        get_db().collection(self.COLLECTION).document(self.id).delete()
        BookCopy._cache_get_all = None

    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            book_id=d.get('book_id', ''),
            library_id=d.get('library_id', ''),
            barcode=d.get('barcode', ''),
            qr_code=d.get('qr_code', ''),
            status=d.get('status', 'AVAILABLE'),
            condition=d.get('condition', 'NEW'),
            condition_notes=d.get('condition_notes', ''),
            building=d.get('building', ''),
            floor=d.get('floor', ''),
            section=d.get('section', ''),
            rack=d.get('rack', ''),
            shelf=d.get('shelf', ''),
            position=d.get('position', ''),
            created_at=d.get('created_at'),
            updated_at=d.get('updated_at'),
        )

    @classmethod
    def get_by_id(cls, copy_id):
        doc = get_db().collection(cls.COLLECTION).document(copy_id).get()
        if doc.exists:
            return cls._from_doc(doc)
        return None

    @classmethod
    def get_by_book(cls, book_id):
        docs = get_db().collection(cls.COLLECTION).where('book_id', '==', book_id).stream()
        return [cls._from_doc(d) for d in docs if d.to_dict()]

    @classmethod
    def get_by_library(cls, library_id):
        docs = get_db().collection(cls.COLLECTION).where('library_id', '==', library_id).stream()
        return [cls._from_doc(d) for d in docs if d.to_dict()]

    _cache_get_all = None
    _cache_get_all_time = 0

    @classmethod
    def get_all(cls):
        import time
        if cls._cache_get_all is not None and (time.time() - cls._cache_get_all_time) < 300:
            return cls._cache_get_all
            
        docs = get_db().collection(cls.COLLECTION).stream()
        copies = [cls._from_doc(d) for d in docs if d.to_dict()]
        
        cls._cache_get_all = copies
        cls._cache_get_all_time = time.time()
        return copies
