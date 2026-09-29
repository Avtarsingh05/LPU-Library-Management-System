"""
Notification model.
Collection: 'notifications'
"""
from models import get_db
from datetime import datetime
import uuid
import time

_notif_cache = {}
_NOTIF_TTL = 300

class Notification:
    COLLECTION = 'notifications'

    def __init__(self, id=None, user_id='', title='', message='', type='info',
                 is_read=False, created_at=None):
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.title = title
        self.message = message
        self.type = type # info, warning, danger, success
        self.is_read = is_read
        self.created_at = created_at or datetime.utcnow()

    def _to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at,
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        if self.user_id in _notif_cache: del _notif_cache[self.user_id]
        return self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        if self.user_id in _notif_cache: del _notif_cache[self.user_id]
        return self

    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            user_id=d.get('user_id', ''),
            title=d.get('title', ''),
            message=d.get('message', ''),
            type=d.get('type', 'info'),
            is_read=d.get('is_read', False),
            created_at=d.get('created_at'),
        )

    @classmethod
    def get_by_user(cls, user_id, unread_only=False):
        now = time.time()
        cache_key = user_id
        if cache_key in _notif_cache:
            ts, all_notifs = _notif_cache[cache_key]
            if now - ts < _NOTIF_TTL:
                if unread_only: return [n for n in all_notifs if not n.is_read]
                return all_notifs
        docs = get_db().collection(cls.COLLECTION).where('user_id', '==', user_id).stream()
        notifs = [cls._from_doc(d) for d in docs if d.to_dict()]
        notifs.sort(key=lambda n: n.created_at or datetime.min, reverse=True)
        _notif_cache[cache_key] = (now, notifs)
        if unread_only: return [n for n in notifs if not n.is_read]
        return notifs

