"""
LibrarianAssignment model to map librarians to libraries.
Collection: 'librarianAssignments'
"""
from models import get_db
from datetime import datetime
import uuid

class LibrarianAssignment:
    COLLECTION = 'librarianAssignments'

    def __init__(self, id=None, librarian_id='', library_id='', assigned_at=None):
        self.id = id or str(uuid.uuid4())
        self.librarian_id = librarian_id
        self.library_id = library_id
        self.assigned_at = assigned_at or datetime.utcnow()

    def _to_dict(self):
        return {
            'id': self.id,
            'librarian_id': self.librarian_id,
            'library_id': self.library_id,
            'assigned_at': self.assigned_at,
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        return self
    
    def delete(self):
        get_db().collection(self.COLLECTION).document(self.id).delete()

    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            librarian_id=d.get('librarian_id', ''),
            library_id=d.get('library_id', ''),
            assigned_at=d.get('assigned_at'),
        )

    @classmethod
    def get_by_librarian(cls, librarian_id):
        docs = get_db().collection(cls.COLLECTION).where('librarian_id', '==', librarian_id).stream()
        return [cls._from_doc(d) for d in docs if d.to_dict()]

    @classmethod
    def get_by_library(cls, library_id):
        docs = get_db().collection(cls.COLLECTION).where('library_id', '==', library_id).stream()
        return [cls._from_doc(d) for d in docs if d.to_dict()]

    @classmethod
    def remove_assignment(cls, librarian_id, library_id):
        docs = get_db().collection(cls.COLLECTION).where('librarian_id', '==', librarian_id).where('library_id', '==', library_id).stream()
        for doc in docs:
            doc.reference.delete()
