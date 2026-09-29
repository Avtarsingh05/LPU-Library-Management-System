"""
Setting model backed by Firestore.
Collection: 'settings'
Document ID: the setting key itself (e.g. 'library_name')
"""
from models import get_db


class Setting:
    COLLECTION = 'settings'

    @staticmethod
    def get(key, default=None):
        try:
            doc = get_db().collection(Setting.COLLECTION).document(key).get()
            if doc.exists:
                return doc.to_dict().get('value', default)
        except Exception:
            pass
        return default

    @staticmethod
    def set(key, value):
        try:
            get_db().collection(Setting.COLLECTION).document(key).set({
                'key': key,
                'value': str(value),
            })
        except Exception:
            pass

    def __repr__(self):
        return f'<Setting>'
