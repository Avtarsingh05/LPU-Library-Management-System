from . import db

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500))
    description = db.Column(db.String(200))
    
    @staticmethod
    def get(key, default=None):
        try:
            setting = Setting.query.filter_by(key=key).first()
            return setting.value if setting else default
        except Exception:
            return default
    
    @staticmethod
    def set(key, value):
        try:
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
            else:
                setting = Setting(key=key, value=str(value))
                db.session.add(setting)
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass
    
    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'
