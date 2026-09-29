"""
Fine model backed by Firestore.
Collection: 'fines'
"""
from models import get_db
from datetime import datetime
import uuid


class Fine:
    COLLECTION = 'fines'

    def __init__(self, id=None, issue_id='', member_id='', amount=0.0,
                 reason='Overdue return', status='pending',
                 created_at=None, paid_date=None,
                 issue=None, member=None):
        self.id = id or str(uuid.uuid4())
        self.issue_id = issue_id
        self.member_id = member_id
        self.amount = float(amount or 0.0)
        self.reason = reason
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.paid_date = paid_date
        self._issue = issue
        self._member = member

    @property
    def issue(self):
        if self._issue is None and self.issue_id:
            from models.issue import Issue
            self._issue = Issue.get_by_id(self.issue_id)
        return self._issue

    @property
    def member(self):
        if self._member is None and self.member_id:
            from models.member import Member
            self._member = Member.get_by_id(self.member_id)
        return self._member

    # ── Persistence ──────────────────────────────────────────────────────────
    def _to_dict(self):
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            'member_id': self.member_id,
            'amount': self.amount,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at,
            'paid_date': self.paid_date,
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        Fine._cache_get_all = {}
        return self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        Fine._cache_get_all = {}
        return self

    # ── Class-level queries ──────────────────────────────────────────────────
    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            issue_id=d.get('issue_id', ''),
            member_id=d.get('member_id', ''),
            amount=d.get('amount', 0.0),
            reason=d.get('reason', 'Overdue return'),
            status=d.get('status', 'pending'),
            created_at=d.get('created_at'),
            paid_date=d.get('paid_date'),
        )

    @classmethod
    def get_by_id(cls, fid):
        doc = get_db().collection(cls.COLLECTION).document(fid).get()
        if doc.exists:
            return cls._from_doc(doc)
        return None

    _cache_get_all = {}
    _cache_get_all_time = {}

    @classmethod
    def get_all(cls, status=None):
        import time
        cache_key = status or 'all'
        if cache_key in cls._cache_get_all and (time.time() - cls._cache_get_all_time.get(cache_key, 0)) < 30:
            return cls._cache_get_all[cache_key]

        q = get_db().collection(cls.COLLECTION)
        if status:
            q = q.where('status', '==', status)
        docs = q.stream()
        fines = [cls._from_doc(d) for d in docs if d.to_dict()]
        fines.sort(key=lambda f: f.created_at or datetime.min, reverse=True)
        
        cls._cache_get_all[cache_key] = fines
        cls._cache_get_all_time[cache_key] = time.time()
        
        return fines

    @classmethod
    def get_by_member(cls, member_id, status=None):
        q = get_db().collection(cls.COLLECTION).where('member_id', '==', member_id)
        if status:
            q = q.where('status', '==', status)
        docs = q.stream()
        fines = [cls._from_doc(d) for d in docs if d.to_dict()]
        fines.sort(key=lambda f: f.created_at or datetime.min, reverse=True)
        return fines

    @classmethod
    def search(cls, query_text='', status=''):
        all_fines = cls.get_all(status=status if status else None)
        if not query_text:
            return all_fines
        q = query_text.lower()
        result = []
        for f in all_fines:
            m = f.member
            if m and (q in m.name.lower() or q in m.member_id.lower()):
                result.append(f)
        return result

    @classmethod
    def total_amount(cls, status):
        """Sum of fine amounts for given status."""
        docs = get_db().collection(cls.COLLECTION).where('status', '==', status).stream()
        return sum(d.to_dict().get('amount', 0) for d in docs if d.to_dict())

    def __repr__(self):
        return f'<Fine {self.id}: ₹{self.amount}>'
