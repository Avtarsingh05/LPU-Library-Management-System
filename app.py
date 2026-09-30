from flask import Flask
import sys
import traceback

def create_app(config_name='default'):
    app = Flask(__name__)
    
    try:
        from config import config
        import os
        from extensions import limiter
        
        app.config.from_object(config[config_name])
        limiter.init_app(app)

        app.config['RAZORPAY_KEY_ID'] = os.environ.get('RAZORPAY_KEY_ID', '')
        app.config['RAZORPAY_KEY_SECRET'] = os.environ.get('RAZORPAY_KEY_SECRET', '')

        import cloudinary
        cloudinary.config(
            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
            api_key = os.environ.get('CLOUDINARY_API_KEY', ''),
            api_secret = os.environ.get('CLOUDINARY_API_SECRET', '')
        )

        from routes.auth import auth_bp
        from routes.dashboard import dashboard_bp
        from routes.books import books_bp
        from routes.members import members_bp
        from routes.issues import issues_bp
        from routes.fines import fines_bp
        from routes.reservations import reservations_bp
        from routes.reports import reports_bp
        from routes.settings import settings_bp
        from routes.libraries import libraries_bp
        from routes.e_library import elibrary_bp
        from routes.ai_assistant import ai_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(books_bp)
        app.register_blueprint(members_bp)
        app.register_blueprint(issues_bp)
        app.register_blueprint(fines_bp)
        app.register_blueprint(reservations_bp)
        app.register_blueprint(reports_bp)
        app.register_blueprint(settings_bp)
        app.register_blueprint(libraries_bp)
        app.register_blueprint(elibrary_bp)
        app.register_blueprint(ai_bp)

        from flask import render_template, session, request
        @app.context_processor
        def inject_globals():
            from flask import current_app
            user = None
            notifications = []
            library_name = 'LPU Library'
            try:
                if 'user_id' in session:
                    from models.user import User
                    user = User.get_by_id(str(session['user_id']))
                    if user:
                        from models.notification import Notification
                        db_notifs = Notification.get_by_user(user.id, unread_only=True)
                        for n in db_notifs:
                            notifications.append({
                                'id': n.id,
                                'type': n.type,
                                'message': n.message,
                                'title': n.title
                            })
                if user and user.is_admin():
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
                        overdue = [i for i in Issue.get_by_member(member.id, status='issued') if i.is_overdue]
                        if overdue:
                            notifications.append({
                                'type': 'danger',
                                'message': f'You have {len(overdue)} overdue book(s)'
                            })
            except Exception as e:
                pass
            
            try:
                from models.setting import Setting
                val = Setting.get('library_name', 'LPU Library')
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
            return dict(current_user=user, notifications=notifications, library_name=library_name, firebase_config=firebase_config)

        @app.errorhandler(404)
        def not_found(e):
            return render_template('errors/404.html'), 404
        @app.errorhandler(403)
        def forbidden(e):
            return render_template('errors/403.html'), 403
        @app.errorhandler(429)
        def ratelimit_handler(e):
            return render_template('errors/429.html', error=e), 429
            
        @app.route('/')
        def index():
            from flask import redirect, url_for
            if 'user_id' in session:
                return redirect(url_for('dashboard.index'))
            return render_template('login.html')
            
    except Exception as e:
        error_trace = traceback.format_exc()
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def catch_all(path):
            return f"<h1>App Crashed During Initialization!</h1><pre>{error_trace}</pre>", 500
            
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

