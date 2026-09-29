"""
User model backed by Firestore.
Collection: 'users'
Document ID: auto-generated UUID
"""
from models import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid


import time
_CACHE_TTL = 300
_cache_get_by_id = {}

class User:
    COLLECTION = 'users'

    def __init__(self, id=None, name='', email='', role='member',
                 password_hash='', is_active=True, created_at=None, profile_pic=''):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.email = email
        self.role = role
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.profile_pic = profile_pic

    # ── Password helpers ─────────────────────────────────────────────────────
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role in ['admin', 'super_admin']

    def is_super_admin(self):
        return self.role == 'super_admin'

    def is_librarian(self):
        return self.role == 'librarian'

    def get_assigned_library_ids(self):
        if self.is_super_admin():
            return None # All libraries
        if self.is_librarian():
            from models.librarian_assignment import LibrarianAssignment
            assignments = LibrarianAssignment.get_by_librarian(self.id)
            return [a.library_id for a in assignments]
        return []

    # ── Persistence ──────────────────────────────────────────────────────────
    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        _cache_get_by_id[self.id] = (time.time(), self)
        return self

    def _to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'password_hash': self.password_hash,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'profile_pic': self.profile_pic,
        }

    # ── Class-level queries ──────────────────────────────────────────────────
    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            name=d.get('name', ''),
            email=d.get('email', ''),
            role=d.get('role', 'member'),
            password_hash=d.get('password_hash', ''),
            is_active=d.get('is_active', True),
            created_at=d.get('created_at'),
            profile_pic=d.get('profile_pic', ''),
        )

    @classmethod
    def get_by_id(cls, uid):
        now = time.time()
        if uid in _cache_get_by_id:
            ts, user = _cache_get_by_id[uid]
            if now - ts < _CACHE_TTL:
                return user
        doc = get_db().collection(cls.COLLECTION).document(uid).get()
        if doc.exists:
            user = cls._from_doc(doc)
            _cache_get_by_id[uid] = (now, user)
            return user
        return None

    @classmethod
    def get_by_email(cls, email):
        """Fetch first user with matching email."""
        docs = get_db().collection(cls.COLLECTION)\
                       .where('email', '==', email).limit(1).stream()
        for doc in docs:
            return cls._from_doc(doc)
        return None

    @classmethod
    def get_all(cls):
        docs = get_db().collection(cls.COLLECTION).stream()
        return [cls._from_doc(d) for d in docs if d.exists]

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        _cache_get_by_id[self.id] = (time.time(), self)

    def __repr__(self):
        return f'<User {self.email}>'

