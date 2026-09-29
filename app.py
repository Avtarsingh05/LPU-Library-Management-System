from flask import Flask, render_template, session
from models import db
from models.user import User
from models.book import Book
from models.member import Member
from models.issue import Issue, Reservation
from models.fine import Fine
from models.setting import Setting
from config import config
import os

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.books import books_bp
    from routes.members import members_bp
    from routes.issues import issues_bp
    from routes.fines import fines_bp
    from routes.reservations import reservations_bp
    from routes.reports import reports_bp
    from routes.settings import settings_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(fines_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    
    # Context processor
    @app.context_processor
    def inject_globals():
        user = None
        notifications = []
        library_name = 'LPU Library Management'
        
        try:
            if 'user_id' in session:
                user = User.query.get(session['user_id'])
            
            if user and user.role == 'admin':
                from models.issue import Issue
                from datetime import date
                today = date.today()
                overdue_count = Issue.query.filter(
                    Issue.status == 'issued',
                    Issue.due_date < today
                ).count()
                if overdue_count > 0:
                    notifications.append({'type': 'danger', 'message': f'{overdue_count} book(s) are overdue'})
            elif user:
                from models.member import Member
                from models.issue import Issue
                from datetime import date
                member = Member.query.filter_by(email=user.email).first()
                if member:
                    overdue = Issue.query.filter(
                        Issue.member_id == member.id,
                        Issue.status == 'issued',
                        Issue.due_date < date.today()
                    ).count()
                    if overdue > 0:
                        notifications.append({'type': 'danger', 'message': f'You have {overdue} overdue book(s)'})
        except Exception:
            pass
            
        try:
            from models.setting import Setting
            val = Setting.get('library_name', 'LPU Library Management')
            if val:
                library_name = val
        except Exception:
            pass
        
        from flask import current_app
        firebase_config = {
            'apiKey': current_app.config.get('FIREBASE_API_KEY') or '',
            'authDomain': current_app.config.get('FIREBASE_AUTH_DOMAIN') or '',
            'projectId': current_app.config.get('FIREBASE_PROJECT_ID') or '',
            'storageBucket': current_app.config.get('FIREBASE_STORAGE_BUCKET') or '',
            'messagingSenderId': current_app.config.get('FIREBASE_MESSAGING_SENDER_ID') or '',
            'appId': current_app.config.get('FIREBASE_APP_ID') or ''
        }
        return dict(current_user=user, notifications=notifications, library_name=library_name, firebase_config=firebase_config)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def server_error(e):
        try:
            return render_template('errors/500.html'), 500
        except Exception:
            return "Internal Server Error", 500
    
    with app.app_context():
        try:
            db.create_all()
            from models.user import User
            admin = User.query.filter_by(email='avtar10@admin.com').first()
            if not admin:
                admin = User(name='System Admin', email='avtar10@admin.com', role='admin')
                admin.set_password('Avtar@10')
                db.session.add(admin)
                db.session.commit()
            else:
                admin.set_password('Avtar@10')
                db.session.commit()
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            app.logger.warning(f"Database initialization warning: {e}")
    
    return app

app = create_app()
handler = app

if __name__ == '__main__':
    app.run(debug=True)
