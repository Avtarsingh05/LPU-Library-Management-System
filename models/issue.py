"""
Issue and Reservation models backed by Firestore.
Collections: 'issues', 'reservations'
"""
from models import get_db
from datetime import datetime, date
import uuid


def _to_date(val):
    """Convert Firestore timestamp or ISO string to date."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if hasattr(val, 'date'):
        return val.date()  # datetime → date
    if isinstance(val, str):
        try:
            return date.fromisoformat(val)
        except Exception:
            pass
    return None


class Issue:
    COLLECTION = 'issues'

    def __init__(self, id=None, book_id='', member_id='', issued_by='',
                 issue_date=None, due_date=None, return_date=None,
                 status='issued', fine_amount=0.0,
                 # eager-loaded related objects (set by route helpers)
                 book=None, member=None):
        self.id = id or str(uuid.uuid4())
        self.book_id = book_id
        self.member_id = member_id
        self.issued_by = issued_by
        self.issue_date = _to_date(issue_date) or date.today()
        self.due_date = _to_date(due_date)
        self.return_date = _to_date(return_date)
        self.status = status
        self.fine_amount = fine_amount or 0.0
        # Related objects (loaded on demand via property)
        self._book = book
        self._member = member

    @property
    def book(self):
        if self._book is None and self.book_id:
            from models.book import Book
            self._book = Book.get_by_id(self.book_id)
        return self._book

    @property
    def member(self):
        if self._member is None and self.member_id:
            from models.member import Member
            self._member = Member.get_by_id(self.member_id)
        return self._member

    @property
    def is_overdue(self):
        if self.status == 'issued' and self.due_date:
            return date.today() > self.due_date
        return False

    @property
    def overdue_days(self):
        if self.is_overdue and self.due_date:
            return (date.today() - self.due_date).days
        if self.status == 'returned' and self.return_date and self.due_date:
            if self.return_date > self.due_date:
                return (self.return_date - self.due_date).days
        return 0

    @property
    def days_remaining(self):
        if self.status == 'issued' and self.due_date:
            return (self.due_date - date.today()).days
        return 0

    # ── Persistence ──────────────────────────────────────────────────────────
    def _to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'member_id': self.member_id,
            'issued_by': self.issued_by,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'status': self.status,
            'fine_amount': self.fine_amount,
            'created_at': datetime.utcnow(),
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        return self

    def update(self, **kwargs):
        update_data = {}
        for k, v in kwargs.items():
            setattr(self, k, v)
            # Serialize dates
            if isinstance(v, date):
                update_data[k] = v.isoformat()
            else:
                update_data[k] = v
        get_db().collection(self.COLLECTION).document(self.id).update(update_data)
        return self

    # ── Class-level queries ──────────────────────────────────────────────────
    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            book_id=d.get('book_id', ''),
            member_id=d.get('member_id', ''),
            issued_by=d.get('issued_by', ''),
            issue_date=d.get('issue_date'),
            due_date=d.get('due_date'),
            return_date=d.get('return_date'),
            status=d.get('status', 'issued'),
            fine_amount=d.get('fine_amount', 0.0),
        )

    @classmethod
    def get_by_id(cls, iid):
        doc = get_db().collection(cls.COLLECTION).document(iid).get()
        if doc.exists:
            return cls._from_doc(doc)
        return None

    @classmethod
    def get_all(cls, status=None):
        q = get_db().collection(cls.COLLECTION)
        if status:
            q = q.where('status', '==', status)
        docs = q.stream()
        issues = [cls._from_doc(d) for d in docs if d.to_dict()]
        # Sort newest first by created_at (stored as timestamp)
        issues.sort(key=lambda i: i.issue_date or date.min, reverse=True)
        return issues

    @classmethod
    def get_by_member(cls, member_id, status=None):
        q = get_db().collection(cls.COLLECTION).where('member_id', '==', member_id)
        if status:
            q = q.where('status', '==', status)
        docs = q.stream()
        return [cls._from_doc(d) for d in docs if d.to_dict()]

    @classmethod
    def get_by_book(cls, book_id, status=None):
        q = get_db().collection(cls.COLLECTION).where('book_id', '==', book_id)
        if status:
            q = q.where('status', '==', status)
        docs = q.stream()
        return [cls._from_doc(d) for d in docs if d.to_dict()]

    @classmethod
    def get_overdue(cls):
        today_str = date.today().isoformat()
        docs = get_db().collection(cls.COLLECTION)\
                       .where('status', '==', 'issued').stream()
        issues = []
        for doc in docs:
            d = doc.to_dict()
            if d and d.get('due_date', '9999-12-31') < today_str:
                issues.append(cls._from_doc(doc))
        issues.sort(key=lambda i: i.due_date or date.min)
        return issues

    @classmethod
    def count(cls, status=None):
        return len(cls.get_all(status=status))

    @classmethod
    def search(cls, query_text='', status=None):
        all_issues = cls.get_all(status=status)
        if not query_text:
            return all_issues
        q = query_text.lower()
        result = []
        for i in all_issues:
            b = i.book
            m = i.member
            if (b and q in b.title.lower()) or \
               (m and q in m.name.lower()) or \
               (m and q in m.member_id.lower()):
                result.append(i)
        return result

    def __repr__(self):
        return f'<Issue {self.id}>'


# ─────────────────────────────────────────────────────────────────────────────

class Reservation:
    COLLECTION = 'reservations'

    def __init__(self, id=None, book_id='', member_id='',
                 reservation_date=None, status='pending',
                 book=None, member=None):
        self.id = id or str(uuid.uuid4())
        self.book_id = book_id
        self.member_id = member_id
        self.reservation_date = reservation_date or datetime.utcnow()
        self.status = status
        self._book = book
        self._member = member

    @property
    def book(self):
        if self._book is None and self.book_id:
            from models.book import Book
            self._book = Book.get_by_id(self.book_id)
        return self._book

    @property
    def member(self):
        if self._member is None and self.member_id:
            from models.member import Member
            self._member = Member.get_by_id(self.member_id)
        return self._member

    def _to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'member_id': self.member_id,
            'reservation_date': self.reservation_date,
            'status': self.status,
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        return self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        return self

    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            book_id=d.get('book_id', ''),
            member_id=d.get('member_id', ''),
            reservation_date=d.get('reservation_date'),
            status=d.get('status', 'pending'),
        )

    @classmethod
    def get_by_id(cls, rid):
        doc = get_db().collection(cls.COLLECTION).document(rid).get()
        if doc.exists:
            return cls._from_doc(doc)
        return None

    @classmethod
    def get_all(cls, status=None):
        q = get_db().collection(cls.COLLECTION)
        if status:
            q = q.where('status', '==', status)
        docs = q.stream()
        reservations = [cls._from_doc(d) for d in docs if d.to_dict()]
        reservations.sort(
            key=lambda r: r.reservation_date or datetime.min, reverse=True
        )
        return reservations

    @classmethod
    def get_by_member(cls, member_id, statuses=None):
        q = get_db().collection(cls.COLLECTION).where('member_id', '==', member_id)
        docs = q.stream()
        res = [cls._from_doc(d) for d in docs if d.to_dict()]
        if statuses:
            res = [r for r in res if r.status in statuses]
        res.sort(key=lambda r: r.reservation_date or datetime.min, reverse=True)
        return res

    @classmethod
    def get_by_book(cls, book_id, status=None):
        q = get_db().collection(cls.COLLECTION).where('book_id', '==', book_id)
        if status:
            q = q.where('status', '==', status)
        docs = q.stream()
        res = [cls._from_doc(d) for d in docs if d.to_dict()]
        res.sort(key=lambda r: r.reservation_date or datetime.min)
        return res

    @classmethod
    def get_active_for_member_book(cls, book_id, member_id):
        """Check if a member already has an active reservation for a book."""
        q = get_db().collection(cls.COLLECTION)\
                    .where('book_id', '==', book_id)\
                    .where('member_id', '==', member_id)
        docs = q.stream()
        for doc in docs:
            r = cls._from_doc(doc)
            if r and r.status in ('pending', 'available'):
                return r
        return None

    def __repr__(self):
        return f'<Reservation {self.id}>'
