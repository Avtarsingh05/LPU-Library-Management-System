"""
Library model backed by Firestore.
Collection: 'libraries'
"""
from models import get_db
from datetime import datetime
import uuid

class Library:
    COLLECTION = 'libraries'

    def __init__(self, id=None, name='', code='', description='', address='',
                 contact_email='', contact_phone='', opening_time='', closing_time='',
                 status='active', created_at=None, updated_at=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.code = code
        self.description = description
        self.address = address
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.opening_time = opening_time
        self.closing_time = closing_time
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def _to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'address': self.address,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'opening_time': self.opening_time,
            'closing_time': self.closing_time,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def save(self):
        self.updated_at = datetime.utcnow()
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        Library._cache_get_all = None
        return self

    def update(self, **kwargs):
        kwargs['updated_at'] = datetime.utcnow()
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        Library._cache_get_all = None
        return self

    def delete(self):
        get_db().collection(self.COLLECTION).document(self.id).delete()
        Library._cache_get_all = None

    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            name=d.get('name', ''),
            code=d.get('code', ''),
            description=d.get('description', ''),
            address=d.get('address', ''),
            contact_email=d.get('contact_email', ''),
            contact_phone=d.get('contact_phone', ''),
            opening_time=d.get('opening_time', ''),
            closing_time=d.get('closing_time', ''),
            status=d.get('status', 'active'),
            created_at=d.get('created_at'),
            updated_at=d.get('updated_at'),
        )

    @classmethod
    def get_by_id(cls, lib_id):
        doc = get_db().collection(cls.COLLECTION).document(lib_id).get()
        if doc.exists:
            return cls._from_doc(doc)
        return None

    _cache_get_all = None
    _cache_get_all_time = 0

    @classmethod
    def get_all(cls):
        import time
        if cls._cache_get_all is not None and (time.time() - cls._cache_get_all_time) < 300:
            return cls._cache_get_all
            
        docs = get_db().collection(cls.COLLECTION).stream()
        libraries = [cls._from_doc(d) for d in docs if d.to_dict()]
        
        cls._cache_get_all = libraries
        cls._cache_get_all_time = time.time()
        return libraries
