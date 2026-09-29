"""
EResource model for E-Library resources.
Collection: 'eLibraryResources'
"""
from models import get_db
from datetime import datetime
import uuid

class EResource:
    COLLECTION = 'eLibraryResources'

    def __init__(self, id=None, title='', description='', category='',
                 author='', library_id='', file_url='', storage_path='',
                 uploaded_by='', access_level='PUBLIC', status='ACTIVE',
                 created_at=None):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.category = category
        self.author = author
        self.library_id = library_id
        self.file_url = file_url
        self.storage_path = storage_path
        self.uploaded_by = uploaded_by
        self.access_level = access_level # PUBLIC, MEMBERS_ONLY, LIBRARY_ONLY, ADMIN_ONLY
        self.status = status
        self.created_at = created_at or datetime.utcnow()

    def _to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'author': self.author,
            'library_id': self.library_id,
            'file_url': self.file_url,
            'storage_path': self.storage_path,
            'uploaded_by': self.uploaded_by,
            'access_level': self.access_level,
            'status': self.status,
            'created_at': self.created_at,
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        EResource._cache_get_all = None
        return self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        EResource._cache_get_all = None
        return self

    def delete(self):
        get_db().collection(self.COLLECTION).document(self.id).delete()
        EResource._cache_get_all = None

    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            title=d.get('title', ''),
            description=d.get('description', ''),
            category=d.get('category', ''),
            author=d.get('author', ''),
            library_id=d.get('library_id', ''),
            file_url=d.get('file_url', ''),
            storage_path=d.get('storage_path', ''),
            uploaded_by=d.get('uploaded_by', ''),
            access_level=d.get('access_level', 'PUBLIC'),
            status=d.get('status', 'ACTIVE'),
            created_at=d.get('created_at'),
        )

    @classmethod
    def get_by_id(cls, rid):
        doc = get_db().collection(cls.COLLECTION).document(rid).get()
        if doc.exists:
            return cls._from_doc(doc)
        return None

    _cache_get_all = None
    _cache_get_all_time = 0

    @classmethod
    def get_all(cls):
        import time
        if cls._cache_get_all is not None and (time.time() - cls._cache_get_all_time) < 60:
            return cls._cache_get_all
            
        docs = get_db().collection(cls.COLLECTION).stream()
        resources = [cls._from_doc(d) for d in docs if d.to_dict()]
        
        cls._cache_get_all = resources
        cls._cache_get_all_time = time.time()
        return resources
