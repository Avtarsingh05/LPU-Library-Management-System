"""
AuditLog model to track important actions.
Collection: 'auditLogs'
"""
from models import get_db
from datetime import datetime
import uuid

class AuditLog:
    COLLECTION = 'auditLogs'

    def __init__(self, id=None, actor_id='', actor_role='', library_id='',
                 action='', entity_type='', entity_id='', timestamp=None, metadata=None):
        self.id = id or str(uuid.uuid4())
        self.actor_id = actor_id
        self.actor_role = actor_role
        self.library_id = library_id
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def _to_dict(self):
        return {
            'id': self.id,
            'actor_id': self.actor_id,
            'actor_role': self.actor_role,
            'library_id': self.library_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        return self

    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            actor_id=d.get('actor_id', ''),
            actor_role=d.get('actor_role', ''),
            library_id=d.get('library_id', ''),
            action=d.get('action', ''),
            entity_type=d.get('entity_type', ''),
            entity_id=d.get('entity_id', ''),
            timestamp=d.get('timestamp'),
            metadata=d.get('metadata', {}),
        )

    @classmethod
    def get_by_library(cls, library_id, limit=50):
        docs = get_db().collection(cls.COLLECTION).where('library_id', '==', library_id).order_by('timestamp', direction='DESCENDING').limit(limit).stream()
        return [cls._from_doc(d) for d in docs if d.to_dict()]
