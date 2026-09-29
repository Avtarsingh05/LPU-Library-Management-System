import os

with open('routes/auth.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the beginning of POST block in login()
old_logic = """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember_me') == 'on'
        
        if not email or not password:
"""

new_logic = """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember_me') == 'on'
        id_token = request.form.get('firebase_id_token')
        
        from flask import current_app
        import requests
        api_key = current_app.config.get('FIREBASE_API_KEY')
        
        # --- Handle Google Sign-in via id_token ---
        if id_token and api_key and api_key != 'your_firebase_api_key_here':
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
            try:
                r = requests.post(url, json={"idToken": id_token}, timeout=10)
                if r.status_code == 200:
                    user_data = r.json().get('users', [{}])[0]
                    google_email = user_data.get('email')
                    google_name = user_data.get('displayName', 'Google User')
                    
                    user = User.query.filter_by(email=google_email).first()
                    if not user:
                        # Auto-create member if they login via Google
                        import os as built_in_os
                        user = User(name=google_name, email=google_email, role='member')
                        user.set_password('generated_' + built_in_os.urandom(8).hex())
                        db.session.add(user)
                        db.session.flush()
                        
                        from routes.members import generate_member_id
                        from models.member import Member
                        member_id = generate_member_id()
                        while Member.query.filter_by(member_id=member_id).first():
                            member_id = generate_member_id()
                        member = Member(member_id=member_id, user_id=user.id, name=google_name, email=google_email)
                        db.session.add(member)
                        db.session.commit()
                        
                    session.permanent = True
                    session['user_id'] = user.id
                    session['user_name'] = user.name
                    session['user_role'] = user.role
                    session['user_email'] = user.email
                    
                    flash(f'Welcome back, {user.name}!', 'success')
                    return redirect(url_for('dashboard.index'))
                else:
                    flash('Google Authentication failed.', 'danger')
                    return render_template('login.html')
            except Exception:
                flash('Authentication service unavailable.', 'danger')
                return render_template('login.html')

        # --- Handle standard Email/Password Sign-in ---
        if not email or not password:
"""

if 'firebase_id_token' not in content:
    content = content.replace(old_logic.strip(), new_logic.strip())
    with open('routes/auth.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("auth.py updated for Google Auth!")
else:
    print("auth.py already has google auth!")
