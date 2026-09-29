from flask import Flask, render_template, session
from config import config
import os


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

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

    # ── Context processor ────────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        from flask import current_app
        user = None
        notifications = []
        library_name = 'LPU Library Management'

        try:
            if 'user_id' in session:
                from models.user import User
                user = User.get_by_id(str(session['user_id']))

            if user and user.role == 'admin':
                from models.issue import Issue
                overdue = Issue.get_overdue()
                if overdue:
                    notifications.append({
                        'type': 'danger',
                        'message': f'{len(overdue)} book(s) are overdue'
                    })
            elif user:
                from models.member import Member
                from models.issue import Issue
                member = Member.get_by_email(user.email)
                if member:
                    overdue = [i for i in Issue.get_by_member(member.id, status='issued')
                               if i.is_overdue]
                    if overdue:
                        notifications.append({
                            'type': 'danger',
                            'message': f'You have {len(overdue)} overdue book(s)'
                        })
        except Exception:
            pass

        try:
            from models.setting import Setting
            val = Setting.get('library_name', 'LPU Library Management')
            if val:
                library_name = val
        except Exception:
            pass

        firebase_config = {
            'apiKey': current_app.config.get('FIREBASE_API_KEY') or '',
            'authDomain': current_app.config.get('FIREBASE_AUTH_DOMAIN') or '',
            'projectId': current_app.config.get('FIREBASE_PROJECT_ID') or '',
            'storageBucket': current_app.config.get('FIREBASE_STORAGE_BUCKET') or '',
            'messagingSenderId': current_app.config.get('FIREBASE_MESSAGING_SENDER_ID') or '',
            'appId': current_app.config.get('FIREBASE_APP_ID') or '',
        }

        return dict(
            current_user=user,
            notifications=notifications,
            library_name=library_name,
            firebase_config=firebase_config,
        )

    # ── Error handlers ───────────────────────────────────────────────────────
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

    # ── Seed admin on startup ────────────────────────────────────────────────
    try:
        from models.user import User
        existing = User.get_by_email('avtar10@admin.com')
        if not existing:
            admin = User(name='System Admin', email='avtar10@admin.com', role='admin')
            admin.set_password('Avtar@10')
            admin.save()
        else:
            # Always ensure password is current
            existing.set_password('Avtar@10')
            existing.save()
    except Exception as e:
        app.logger.warning(f"Admin seed note (Firestore may not be ready): {e}")

    return app


app = create_app()
handler = app

if __name__ == '__main__':
    app.run(debug=True)
