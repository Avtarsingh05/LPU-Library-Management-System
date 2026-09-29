"""
Member model backed by Firestore.
Collection: 'members'
Document ID: auto-generated UUID
"""
from models import get_db
from datetime import datetime
import uuid
import time


class Member:
    COLLECTION = 'members'

    def __init__(self, id=None, member_id='', user_id=None, name='', email='',
                 phone='', department='', course='', semester='', address='',
                 registration_date=None, status='active', 
                 id_card_url='', verification_status='approved', rejection_reason=''):
        self.id = id or str(uuid.uuid4())
        self.member_id = member_id
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.department = department
        self.course = course
        self.semester = semester
        self.address = address
        self.registration_date = registration_date or datetime.utcnow()
        self.status = status
        self.id_card_url = id_card_url
        self.verification_status = verification_status
        self.rejection_reason = rejection_reason

    @property
    def active_issues_count(self):
        from models.issue import Issue
        return len(Issue.get_by_member(self.id, status='issued'))

    @property
    def total_fines(self):
        from models.fine import Fine
        fines = Fine.get_by_member(self.id, status='pending')
        return sum(f.amount for f in fines)

    # ── Persistence ──────────────────────────────────────────────────────────
    def _to_dict(self):
        return {
            'id': self.id,
            'member_id': self.member_id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'course': self.course,
            'semester': self.semester,
            'address': self.address,
            'registration_date': self.registration_date,
            'status': self.status,
            'id_card_url': self.id_card_url,
            'verification_status': self.verification_status,
            'rejection_reason': self.rejection_reason,
        }

    def save(self):
        get_db().collection(self.COLLECTION).document(self.id).set(self._to_dict())
        Member._cache_get_all = None
        return self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        get_db().collection(self.COLLECTION).document(self.id).update(kwargs)
        if hasattr(self.__class__, '_cache_by_uid') and self.user_id in self.__class__._cache_by_uid:
            del self.__class__._cache_by_uid[self.user_id]
        Member._cache_get_all = None
        return self

    # ── Class-level queries ──────────────────────────────────────────────────
    @classmethod
    def _from_doc(cls, doc):
        d = doc.to_dict()
        if not d:
            return None
        return cls(
            id=d.get('id', doc.id),
            member_id=d.get('member_id', ''),
            user_id=d.get('user_id'),
            name=d.get('name', ''),
            email=d.get('email', ''),
            phone=d.get('phone', ''),
            department=d.get('department', ''),
            course=d.get('course', ''),
            semester=d.get('semester', ''),
            address=d.get('address', ''),
            registration_date=d.get('registration_date'),
            status=d.get('status', 'active'),
            id_card_url=d.get('id_card_url', ''),
            verification_status=d.get('verification_status', 'approved'),
            rejection_reason=d.get('rejection_reason', ''),
        )

    @classmethod
    def get_by_id(cls, mid):
        doc = get_db().collection(cls.COLLECTION).document(mid).get()
        if doc.exists:
            return cls._from_doc(doc)
        return None

    @classmethod
    def get_by_email(cls, email):
        docs = get_db().collection(cls.COLLECTION)\
                       .where('email', '==', email).limit(1).stream()
        for doc in docs:
            return cls._from_doc(doc)
        return None

    @classmethod
    def get_by_user_id(cls, user_id):
        if not hasattr(cls, '_cache_by_uid'):
            cls._cache_by_uid = {}
        now = time.time()
        if user_id in cls._cache_by_uid:
            ts, mem = cls._cache_by_uid[user_id]
            if now - ts < 300:
                return mem
        docs = get_db().collection(cls.COLLECTION).where('user_id', '==', user_id).limit(1).stream()
        for doc in docs:
            mem = cls._from_doc(doc)
            cls._cache_by_uid[user_id] = (now, mem)
            return mem
        return None

    @classmethod
    def get_by_member_id(cls, member_id):
        docs = get_db().collection(cls.COLLECTION)\
                       .where('member_id', '==', member_id).limit(1).stream()
        for doc in docs:
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
        members = [cls._from_doc(d) for d in docs if d.to_dict()]
        members.sort(key=lambda m: m.registration_date or datetime.min, reverse=True)
        
        cls._cache_get_all = members
        cls._cache_get_all_time = time.time()
        return members

    @classmethod
    def search(cls, query_text='', status='', department=''):
        all_members = cls.get_all()
        q = query_text.lower() if query_text else ''
        result = []
        for m in all_members:
            if q and not (q in m.name.lower() or q in m.email.lower()
                          or q in m.member_id.lower()
                          or q in (m.phone or '').lower()):
                continue
            if status and m.status != status:
                continue
            if department and m.department != department:
                continue
            result.append(m)
        return result

    @classmethod
    def count(cls):
        try:
            aggr_query = get_db().collection(cls.COLLECTION).count()
            results = aggr_query.get()
            return results[0][0].value
        except Exception:
            docs = get_db().collection(cls.COLLECTION).select([]).stream()
            return sum(1 for _ in docs)

    def __repr__(self):
        return f'<Member {self.member_id}: {self.name}>'


