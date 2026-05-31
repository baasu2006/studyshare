from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import os, requests, urllib.parse
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env file

app = Flask(__name__)
app.secret_key = "secret_notes_key_2026"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ── CONFIG — loaded from .env file ──────────────────────────────────────
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/auth/google/callback")

ANTHROPIC_API_KEY = os.getenv("GROQ_API_KEY", "")       # Groq key from .env
YOUTUBE_API_KEY   = os.getenv("YOUTUBE_API_KEY", "")    # YouTube key from .env
# ────────────────────────────────────────────────────────────────────────

# In-memory DB
users = {
    "student@test.com": {
        "password": "password123", "username": "student",
        "method": "form", "joined": "2026-01-01 00:00:00", "last_login": None
    }
}
ADMIN_EMAIL = "admin@studyshare.com"
users[ADMIN_EMAIL] = {
    "password": "admin2026", "username": "Admin",
    "method": "form", "joined": "2026-01-01 00:00:00", "last_login": None
}

notes_db   = []
login_log  = []

ALLOWED_EXTENSIONS = {'pdf', 'pptx', 'ppt', 'docx', 'doc'}

def allowed_file(f):
    return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def record_login(email, username, method):
    t = now_str()
    users[email]['last_login'] = t
    login_log.append({'email': email, 'username': username, 'time': t, 'method': method})

# ── PAGES ────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html',
        notes=notes_db,
        user=session['user'],
        username=session.get('username', session['user'].split('@')[0]),
        ADMIN_EMAIL=ADMIN_EMAIL)

# ── AUTH: Email/Password ─────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        if email in users and users[email].get('password') == password:
            session['user']     = email
            session['username'] = users[email].get('username', email.split('@')[0])
            record_login(email, session['username'], 'form')
            return redirect(url_for('home'))
        return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html',
        GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID,
        GOOGLE_REDIRECT_URI=GOOGLE_REDIRECT_URI)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username', email.split('@')[0])
        if email in users:
            return render_template('signup.html', error="Account already exists. Please login.")
        users[email] = {"password": password, "username": username,
                        "method": "form", "joined": now_str(), "last_login": None}
        session['user']     = email
        session['username'] = username
        record_login(email, username, 'form')
        return redirect(url_for('home'))
    return render_template('signup.html',
        GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID,
        GOOGLE_REDIRECT_URI=GOOGLE_REDIRECT_URI)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── AUTH: Real Google OAuth 2.0 ──────────────────────────────────────────

@app.route('/auth/google')
def google_auth():
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account"
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return redirect(url)

@app.route('/auth/google/callback')
def google_callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('login'))

    # Exchange code for token
    token_resp = requests.post("https://oauth2.googleapis.com/token", data={
        "code":          code,
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "grant_type":    "authorization_code"
    }).json()

    access_token = token_resp.get('access_token')
    if not access_token:
        return render_template('login.html', error="Google login failed. Try again.")

    # Get user info
    user_info = requests.get("https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email    = user_info.get('email')
    name     = user_info.get('name', email.split('@')[0])
    picture  = user_info.get('picture', '')

    if email not in users:
        users[email] = {"password": None, "username": name, "method": "google",
                        "joined": now_str(), "last_login": None, "picture": picture}
    else:
        users[email]['picture'] = picture

    session['user']     = email
    session['username'] = name
    session['picture']  = picture
    record_login(email, name, 'google')
    return redirect(url_for('home'))

# ── NOTES ────────────────────────────────────────────────────────────────

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    file     = request.files.get('note_file')
    title    = request.form.get('title')
    category = request.form.get('category')
    if category == 'Other':
        category = request.form.get('other_subject', 'Other')
    share_link_enabled = request.form.get('share_link') == 'on'

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        note_id = len(notes_db) + 1
        notes_db.append({
            'id':           note_id,
            'title':        title,
            'category':     category,
            'filename':     filename,
            'author':       session['user'],
            'author_name':  session.get('username', session['user'].split('@')[0]),
            'is_pinned':    False,
            'uploaded_at':  datetime.now().strftime("%b %d, %Y"),
            'share_link':   share_link_enabled,  # admin toggles this
            'is_admin_note': session['user'] == ADMIN_EMAIL
        })
        return redirect(url_for('home'))
    return "File type not allowed! Use PDF, Word, or PPT."

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/pin/<int:note_id>')
def pin_note(note_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    note = next((n for n in notes_db if n['id'] == note_id), None)
    if note and (session['user'] == note['author'] or session['user'] == ADMIN_EMAIL):
        note['is_pinned'] = not note['is_pinned']
    return redirect(url_for('home'))

@app.route('/delete/<int:note_id>')
def delete_note(note_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    note = next((n for n in notes_db if n['id'] == note_id), None)
    if note and (session['user'] == note['author'] or session['user'] == ADMIN_EMAIL):
        notes_db.remove(note)
    return redirect(url_for('home'))

# ── SHARE LINK (public, no login needed) ─────────────────────────────────

@app.route('/share/<int:note_id>')
def share_note(note_id):
    note = next((n for n in notes_db if n['id'] == note_id), None)
    if not note or not note.get('share_link'):
        return "This note is not publicly shared.", 403
    return render_template('share.html', note=note)

# ── AI EXPLAIN (Claude API primary, OpenAI fallback + YouTube) ───────────

SYSTEM_PROMPT = (
    "You are an expert academic tutor. Explain the topic clearly for a student. "
    "Structure your answer in exactly 3 sections separated by newlines:\n"
    "SUMMARY: One sentence overview.\n"
    "KEY CONCEPTS: 2-3 bullet points with simple analogies (use • as bullet).\n"
    "REAL-WORLD EXAMPLE: One concrete everyday example.\n"
    "Keep it under 220 words. Plain text only, no markdown symbols."
)

def explain_with_claude(topic):
    """Primary: Groq API (free) - variable name kept as ANTHROPIC_API_KEY"""
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {ANTHROPIC_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "max_tokens": 500,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Explain: {topic}"}
            ]
        },
        timeout=15
    )
    result = resp.json()
    # Groq uses OpenAI-compatible format
    if "choices" in result and result["choices"]:
        return result["choices"][0]["message"]["content"]
    err = result.get("error", {})
    raise ValueError(err.get("message", str(result)))



@app.route('/api/explain', methods=['POST'])
def api_explain():
    data  = request.get_json()
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400

    # ── AI explanation: try Claude first, then OpenAI ─────────────────────
    ai_text = ""
    ai_source = ""
    if ANTHROPIC_API_KEY and not ANTHROPIC_API_KEY.startswith("YOUR_"):
        try:
            ai_text  = explain_with_claude(topic)
            ai_source = "claude"
        except Exception as e:
            ai_text = f"⚠️ Groq API error: {e}"
            print(f"[Groq API error] {e}")



    if not ai_text:
        ai_text = (
            "⚠️ Groq API key not set or invalid.\n\n"
            "To fix this:\n"
            "1. Go to console.groq.com and sign up for free\n"
            "2. Create an API key (no credit card needed)\n"
            "3. Open app.py and set:\n"
            "   ANTHROPIC_API_KEY = 'gsk_your_key_here'"
        )

    # ── YouTube suggestions ───────────────────────────────────────────────
    videos = []
    if YOUTUBE_API_KEY and YOUTUBE_API_KEY != "YOUR_YOUTUBE_API_KEY":
        try:
            yt = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet", "q": f"{topic} explained tutorial",
                    "type": "video", "maxResults": 3,
                    "relevanceLanguage": "en", "key": YOUTUBE_API_KEY
                },
                timeout=10
            ).json()
            for item in yt.get('items', []):
                vid_id = item['id'].get('videoId')
                if not vid_id:
                    continue
                videos.append({
                    "title":     item['snippet']['title'],
                    "channel":   item['snippet']['channelTitle'],
                    "thumbnail": item['snippet']['thumbnails']['medium']['url'],
                    "url":       f"https://www.youtube.com/watch?v={vid_id}"
                })
        except Exception as e:
            print(f"[YouTube API error] {e}")

    return jsonify({'explanation': ai_text, 'videos': videos, 'source': ai_source})

# ── ADMIN ─────────────────────────────────────────────────────────────────

@app.route('/admin')
def admin_dashboard():
    if session.get('user') != ADMIN_EMAIL:
        return "Access Denied", 403
    return render_template('admin.html',
        all_notes=notes_db, all_users=users,
        login_log=login_log, admin_email=ADMIN_EMAIL)


# ── GROQ KEY TEST (open in browser to verify) ────────────────────────────
@app.route('/api/test-groq')
def test_groq():
    if ANTHROPIC_API_KEY.startswith("YOUR_"):
        return "Key not set. Replace YOUR_GROQ_API_KEY in app.py", 400
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {ANTHROPIC_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant", "max_tokens": 20,
                  "messages": [{"role": "user", "content": "Say OK"}]},
            timeout=10
        ).json()
        if "choices" in resp:
            return f"Groq key works! Reply: {resp['choices'][0]['message']['content']}", 200
        return f"Groq error: {resp.get('error', resp)}", 400
    except Exception as e:
        return f"Connection error: {e}", 500

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
