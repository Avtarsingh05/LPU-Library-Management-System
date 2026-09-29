import os

with open('templates/login.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Google Sign-in button
google_btn = """
        <div style="text-align: center; margin: 1rem 0; color: var(--text-muted); font-size: 0.85rem;">OR</div>
        <button type="button" class="btn btn-outline-secondary w-100" style="display:flex; align-items:center; justify-content:center; gap:0.5rem;" onclick="signInWithGoogle()">
          <svg width="18" height="18" viewBox="0 0 18 18"><path fill="#4285F4" d="M17.64 9.2045c0-.6381-.0573-1.2518-.1636-1.8409H9v3.4814h4.8436c-.2086 1.125-.8427 2.0782-1.7959 2.7164v2.2581h2.9086c1.7018-1.5668 2.6836-3.874 2.6836-6.615z"></path><path fill="#34A853" d="M9 18c2.43 0 4.4673-.806 5.9564-2.1805l-2.9086-2.2581c-.8059.54-1.8368.859-3.0478.859-2.344 0-4.3282-1.5831-5.036-3.7104H.9574v2.3318C2.4382 15.9832 5.4818 18 9 18z"></path><path fill="#FBBC05" d="M3.964 10.71c-.18-.54-.2822-1.1168-.2822-1.71s.1023-1.17.2822-1.71V4.9582H.9574C.3477 6.1732 0 7.5477 0 9s.3477 2.8268.9574 4.0418L3.964 10.71z"></path><path fill="#EA4335" d="M9 3.5795c1.3214 0 2.5077.4541 3.4405 1.346l2.5813-2.5814C13.4632.8918 11.426 0 9 0 5.4818 0 2.4382 2.0168.9574 4.9582L3.964 7.29C4.6718 5.1627 6.656 3.5795 9 3.5795z"></path></svg>
          Sign in with Google
        </button>
      </form>
"""
if "Sign in with Google" not in content:
    content = content.replace('</form>', google_btn)

# Add Firebase JS logic
firebase_js = """
<!-- Firebase JS SDK (v8 compat for simplicity) -->
<script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>
<script>
const firebaseConfig = {
  apiKey: "{{ firebase_config.apiKey }}",
  authDomain: "{{ firebase_config.authDomain }}",
  projectId: "{{ firebase_config.projectId }}",
  storageBucket: "{{ firebase_config.storageBucket }}",
  messagingSenderId: "{{ firebase_config.messagingSenderId }}",
  appId: "{{ firebase_config.appId }}"
};

if (firebaseConfig.apiKey && firebaseConfig.apiKey !== 'your_firebase_api_key_here') {
  firebase.initializeApp(firebaseConfig);
}

function signInWithGoogle() {
  if (!firebaseConfig.apiKey || firebaseConfig.apiKey === 'your_firebase_api_key_here') {
    alert("Firebase is not configured yet. Please configure the .env file with your Google API keys.");
    return;
  }
  var provider = new firebase.auth.GoogleAuthProvider();
  firebase.auth().signInWithPopup(provider).then((result) => {
    result.user.getIdToken().then((idToken) => {
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '{{ url_for("auth.login") }}';
      
      const tokenInput = document.createElement('input');
      tokenInput.type = 'hidden';
      tokenInput.name = 'firebase_id_token';
      tokenInput.value = idToken;
      form.appendChild(tokenInput);
      
      document.body.appendChild(form);
      form.submit();
    });
  }).catch((error) => {
    console.error("Google Login Error", error);
    alert(error.message);
  });
}
</script>
</body>
"""
if "firebase-app.js" not in content:
    content = content.replace('</body>', firebase_js)

with open('templates/login.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('login.html updated for Google Auth!')
